import CryptoKit
import Darwin
import Foundation

@main struct Check {
    static func main() throws {
        let fm = FileManager.default
        let room = fm.temporaryDirectory.appendingPathComponent("gamma-native-\(UUID().uuidString)", isDirectory: true)
        try fm.createDirectory(at: room, withIntermediateDirectories: false, attributes: [.posixPermissions: 0o700])
        defer { try? fm.removeItem(at: room) }
        let original = room.appendingPathComponent("selected.txt")
        let replacement = room.appendingPathComponent("safe-save.txt")
        let unrelated = room.appendingPathComponent("unrelated.txt")
        try Data("old".utf8).write(to: original)
        let tracking = original.withUnsafeFileSystemRepresentation { path in
            path.map { chflags($0, UInt32(UF_TRACKED)) } ?? -1
        }
        precondition(tracking == 0, "Cannot track private fixture")
        guard let selection = SelectedDocument(ownerSelectedURL: original) else {
            fatalError("Cannot bind the private fixture")
        }
        guard let old = selection.observeCurrent() else { fatalError("Expected original evidence") }
        precondition(old.byteLength == 3 && selection.observeCurrent(maxBytes: 2) == nil)
        let writer = try FileHandle(forWritingTo: original)
        try writer.seekToEnd()
        try writer.write(contentsOf: Data("+edit".utf8))
        try writer.close()
        guard let edited = selection.observeCurrent() else { fatalError("Expected same-object edit evidence") }
        precondition(edited.byteLength == 8 && edited != old)
        try Data("Foundation replacement".utf8).write(to: replacement)
        _ = try fm.replaceItemAt(original, withItemAt: replacement)
        let savedBytes = try Data(contentsOf: original)
        precondition(savedBytes == Data("Foundation replacement".utf8))
        precondition(selection.observeCurrent() == nil, "An unproven inode crossing must fail closed")
        guard let reselected = SelectedDocument(ownerSelectedURL: original),
              let saved = reselected.observeCurrent() else { fatalError("Expected evidence after explicit re-selection") }
        let digest = SHA256.hash(data: savedBytes).map { String(format: "%02x", $0) }.joined()
        precondition(saved.sha256 == digest)
        try Data("Foundation replacement".utf8).write(to: unrelated)
        try fm.removeItem(at: original)
        try fm.moveItem(at: unrelated, to: original)
        precondition(reselected.observeCurrent() == nil, "Same name and bytes do not prove logical identity")
        try fm.removeItem(at: original)
        precondition(reselected.observeCurrent() == nil, "Deletion must not yield stale evidence")
        try fm.createSymbolicLink(at: original, withDestinationURL: replacement)
        precondition(selection.observeCurrent() == nil)
        selection.revoke()
        precondition(selection.observeCurrent() == nil)
        print("ok: macOS in-place evidence, Foundation safe save refuses old selection, explicit re-selection works, unrelated identical-byte replacement rejected, deletion, symlink, revoke")
    }
}
