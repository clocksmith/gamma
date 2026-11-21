import AppKit
import Foundation

@main struct PickerMain {
    @MainActor static func main() {
        let app = NSApplication.shared
        app.setActivationPolicy(.regular)
        app.activate(ignoringOtherApps: true)
        guard let document = SelectedDocument.pick() else {
            print("{\"status\":\"selection-unavailable\"}")
            return
        }
        defer { document.revoke() }
        guard let evidence = document.observeCurrent() else {
            print("{\"status\":\"selection-unavailable\"}")
            return
        }
        print("{\"status\":\"observed\",\"byteLength\":\(evidence.byteLength),\"sha256\":\"\(evidence.sha256)\"}")
    }
}
