import UIKit

@main
final class AppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?

    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        let window = UIWindow(frame: UIScreen.main.bounds)
        // Native render tests create their own views/devices. Do not start a
        // second asynchronous SpriteKit loader in the injected unit-test host.
        let unitHost = NSClassFromString("XCTestCase") != nil
        let reviewing = ProcessInfo.processInfo.arguments.contains { $0.hasSuffix("Review") }
        if unitHost && !reviewing { window.rootViewController = UIViewController() }
        else {
            window.rootViewController = ProcessInfo.processInfo.arguments.contains("-shadowReview")
                ? ShadowLabViewController() : GameViewController()
        }
        window.makeKeyAndVisible()
        self.window = window
        return true
    }
}

