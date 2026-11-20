import AppKit
import CryptoKit
import Darwin
import Foundation

/// In-process read-only capability; no CLI, path input from recipes, or write receipts.
final class SelectedDocument {
    struct Observation: Equatable {
        let byteLength: Int
        let sha256: String
    }
    private let url: URL
    private let initial: stat
    private let anchor: Int32
    private var active = true

    // Trusted owner host ONLY. Never expose this factory to a recipe or transport.
    init?(ownerSelectedURL url: URL) {
        guard url.isFileURL else { return nil }
        let anchor = Self.openRegularCandidate(url)
        guard anchor >= 0 else { return nil }
        var initial = stat()
        guard fstat(anchor, &initial) == 0, (initial.st_mode & S_IFMT) == S_IFREG else {
            _ = Darwin.close(anchor)
            return nil
        }
        guard let current = Self.readFile(url, limit: 0), Self.sameRevision(initial, current.0) else {
            _ = Darwin.close(anchor)
            return nil
        }
        self.url = url
        self.initial = initial
        self.anchor = anchor // keep the original inode from being recycled during this grant
    }

    deinit { if active { _ = Darwin.close(anchor) } }

    /// Call only in response to the owner explicitly choosing to open a file.
    @MainActor static func pick() -> SelectedDocument? {
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false
        panel.resolvesAliases = false
        guard panel.runModal() == .OK, let url = panel.url else { return nil }
        return SelectedDocument(ownerSelectedURL: url)
    }

    // Calls are serialized by the owner host. No persistent bookmark or opt-in
    // to broader filesystem grants. If current access is gone, return unknown.
    func revoke() {
        guard active else { return }
        active = false
        _ = Darwin.close(anchor)
    }

    func observeCurrent(maxBytes: Int = 1 << 20) -> Observation? {
        guard active, maxBytes > 0, maxBytes <= 16 << 20 else { return nil }
        var result: Observation?
        var failure: NSError?
        NSFileCoordinator(filePresenter: nil).coordinate(readingItemAt: url, options: [], error: &failure) { coordinated in
            // Never authorize an inode crossing. A logical document ID can
            // survive both a safe save and an unrelated replacement at this path.
            guard coordinated.standardizedFileURL == url.standardizedFileURL,
                  let before = Self.readFile(coordinated, limit: 0),
                  initial.st_dev == before.0.st_dev, initial.st_ino == before.0.st_ino,
                  let reading = Self.readFile(coordinated, limit: maxBytes),
                  Self.sameRevision(before.0, reading.0),
                  let current = Self.readFile(coordinated, limit: 0),
                  Self.sameRevision(reading.0, current.0) else { return }
            result = reading.1
        }
        return failure == nil && active ? result : nil
    }

    private static func sameRevision(_ lhs: stat, _ rhs: stat) -> Bool {
        lhs.st_dev == rhs.st_dev && lhs.st_ino == rhs.st_ino &&
        lhs.st_size == rhs.st_size &&
        lhs.st_mtimespec.tv_sec == rhs.st_mtimespec.tv_sec &&
        lhs.st_mtimespec.tv_nsec == rhs.st_mtimespec.tv_nsec &&
        lhs.st_ctimespec.tv_sec == rhs.st_ctimespec.tv_sec &&
        lhs.st_ctimespec.tv_nsec == rhs.st_ctimespec.tv_nsec
    }

    private static func openRegularCandidate(_ url: URL) -> Int32 {
        url.withUnsafeFileSystemRepresentation {
            $0.map { Darwin.open($0, O_RDONLY | O_NOFOLLOW | O_NONBLOCK | O_CLOEXEC) } ?? -1
        }
    }

    /// A zero limit requests metadata only. No symlinks or non-regular files.
    private static func readFile(_ url: URL, limit: Int) -> (stat, Observation?)? {
        let fd = openRegularCandidate(url)
        guard fd >= 0 else { return nil }
        defer { _ = Darwin.close(fd) }
        var before = stat()
        guard fstat(fd, &before) == 0, (before.st_mode & S_IFMT) == S_IFREG else { return nil }
        if limit == 0 { return (before, nil) }
        guard before.st_size >= 0, before.st_size <= limit else { return nil }
        var buffer = [UInt8](repeating: 0, count: 64 * 1024)
        var hash = SHA256()
        var consumed = 0
        while consumed < before.st_size {
            let requested = min(buffer.count, Int(before.st_size) - consumed)
            let count = buffer.withUnsafeMutableBytes { Darwin.read(fd, $0.baseAddress, requested) }
            guard count > 0 else { return nil }
            hash.update(data: Data(buffer.prefix(count)))
            consumed += count
        }
        var after = stat()
        guard fstat(fd, &after) == 0, sameRevision(before, after) else { return nil }
        let digest = hash.finalize().map { String(format: "%02x", $0) }.joined()
        return (after, Observation(byteLength: consumed, sha256: digest))
    }
}
