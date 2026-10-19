import XCTest
import UIKit

final class JourneyUITests: XCTestCase {
    func testMeadowBattlePreviewKeepsReferenceMapBesideLandscapeScene() {
        continueAfterFailure = false
        XCUIDevice.shared.orientation = .landscapeLeft
        let app = XCUIApplication()
        app.launchArguments = ["-visualReview"]
        app.launch()
        let map = app.otherElements["meadowMap"]
        XCTAssertTrue(map.waitForExistence(timeout: 120))
        waitForReady(app, map: map)
        let originalWidth = map.frame.width

        app.buttons["zoomButton"].tap()
        XCTAssertEqual(app.buttons["zoomButton"].value as? String, "125%")
        app.buttons["openBattlePreview"].tap()

        let battlefield = app.otherElements["battleLandscape"]
        XCTAssertTrue(battlefield.waitForExistence(timeout: 15))
        XCTAssertLessThan(map.frame.width, originalWidth * 0.75)
        XCTAssertGreaterThan(battlefield.frame.width, battlefield.frame.height)
        XCTAssertFalse(app.buttons["openGaitTest"].isHittable)
        let previewState = diagnostics(app)
        XCTAssertEqual(previewState["zoom"] as? Double ?? -1, 1, accuracy: 0.001,
                       "The map pane should show its full reference composition")
        XCTAssertGreaterThan(previewState["independentProps"] as? Int ?? 0, 0)
        assertVisibleGround(map, name: "meadow-map-left-of-battle-scene")
        capture("meadow-map-left-battle-scene-right")

        app.buttons["closeBattlePreview"].tap()
        XCTAssertTrue(app.buttons["zoomButton"].waitForExistence(timeout: 15))
        XCTAssertEqual(map.frame.width, originalWidth, accuracy: 1)
        XCTAssertEqual(app.buttons["zoomButton"].value as? String, "125%")
        XCTAssertEqual(diagnostics(app)["zoom"] as? Double ?? -1, 1.25, accuracy: 0.001,
                       "Closing the preview should restore the user's previous map zoom")
        assertVisibleGround(map, name: "meadow-map-after-battle-preview")
    }

    func testActualMapGaitControlsCoverAllDirectionsAndEveryFrame() {
        continueAfterFailure = false
        XCUIDevice.shared.orientation = .landscapeLeft
        let app = XCUIApplication(); app.launchArguments = ["-visualReview"]; app.launch()
        let map = app.otherElements["meadowMap"]
        XCTAssertTrue(map.waitForExistence(timeout: 120)); waitForReady(app, map: map)
        app.buttons["zoomButton"].tap()
        app.buttons["openGaitTest"].tap()
        app.buttons["gaitPause"].tap()
        for facing in [2, 7, 3, 4, 0, 5, 1, 6] {
            app.buttons["gaitDirection\(facing)"].tap()
            XCTAssertEqual(diagnostics(app)["gaitFacing"] as? Int, facing)
            XCTAssertEqual(diagnostics(app)["mode"] as? String, "gaitTest")
            for frame in 1...24 {
                XCTAssertEqual(diagnostics(app)["gaitFrame"] as? Int, frame)
                if [1, 7, 13, 19].contains(frame) { capture("gait-hero-map-dir\(facing)-frame\(frame)") }
                app.buttons["gaitStep"].tap()
            }
            XCTAssertEqual(diagnostics(app)["gaitFrame"] as? Int, 1)
        }
        app.buttons["openGaitTest"].tap()
        XCTAssertNotEqual(diagnostics(app)["mode"] as? String, "gaitTest")
        XCTAssertEqual(app.buttons["zoomButton"].value as? String, "125%")
        assertVisibleGround(map, name: "main-ground-after-gait-review")
    }

    func testLayeredP1ColorwayPreviewRunsBesideOriginalInTheMapScene() {
        continueAfterFailure = false
        XCUIDevice.shared.orientation = .landscapeLeft
        let app = XCUIApplication(); app.launchArguments = ["-visualReview"]; app.launch()
        let map = app.otherElements["meadowMap"]
        XCTAssertTrue(map.waitForExistence(timeout: 120)); waitForReady(app, map: map)
        app.buttons["openGaitTest"].tap()
        app.buttons["gaitPause"].tap()
        app.buttons["gaitLayeredPreview"].tap()
        var state = diagnostics(app)
        XCTAssertEqual(state["layeredPreview"] as? Bool, true)
        XCTAssertEqual(state["layeredPreviewFrameCount"] as? Int, 24)
        XCTAssertEqual(state["gaitFacing"] as? Int, 0)
        capture("layered-p1-original-versus-blue-boots")
        app.buttons["gaitStep"].tap()
        state = diagnostics(app)
        XCTAssertEqual(state["gaitFrame"] as? Int, 2)
        app.buttons["gaitLayeredPreview"].tap()
        XCTAssertEqual(diagnostics(app)["layeredPreview"] as? Bool, false)
        app.buttons["openGaitTest"].tap()
        assertVisibleGround(map, name: "main-ground-after-layered-preview")
    }

    func testForegroundAndShadowReceiverStayAlignedAtEveryZoom() {
        continueAfterFailure = false
        XCUIDevice.shared.orientation = .landscapeLeft
        let app = XCUIApplication()
        app.launchArguments = ["-visualReview", "-alignmentReview"]
        app.launch()
        let map = app.otherElements["meadowMap"]
        XCTAssertTrue(map.waitForExistence(timeout: 120))
        waitForReady(app, map: map)
        assertCameraLandmarks("100")
        for zoom in [125, 150, 175] {
            app.buttons["zoomButton"].tap()
            XCTAssertEqual(app.buttons["zoomButton"].value as? String, "\(zoom)%")
            assertCameraLandmarks("\(zoom)")
        }
        map.pinch(withScale: 1.3, velocity: 1)
        XCTAssertGreaterThanOrEqual(diagnostics(app)["zoom"] as? Double ?? 0, 1.79)
        assertCameraLandmarks("pinch-max")
        app.buttons["resetButton"].tap()
        assertCameraLandmarks("reset")
    }

    private func waitForReady(_ app: XCUIApplication, map: XCUIElement) {
        let ready = XCTNSPredicateExpectation(predicate: NSPredicate(format: "value CONTAINS %@", "\"shadowReady\":true"), object: map)
        let result = XCTWaiter.wait(for: [ready], timeout: 120)
        if result != .completed {
            print("LOADING_FAILURE_STATE", map.value ?? "none")
            let status = app.staticTexts["loadingStatus"]
            print("LOADING_FAILURE_STAGE", status.exists ? status.label : "loading page hidden")
            capture("main-ground-loading-failure")
        }
        XCTAssertEqual(result, .completed)
    }

    /// Red points come from the SpriteKit world; cyan rings are rasterized in
    /// the native receiver shader. Compare actual composited pixels, not just
    /// two copies of the camera formula or a successful zoom-button response.
    private func assertCameraLandmarks(_ name: String) {
        let screenshot = XCUIScreen.main.screenshot()
        guard let image = screenshot.image.cgImage else { return XCTFail("Missing alignment screen") }
        let factor = min(1.0, 512.0 / Double(max(image.width, image.height)))
        let width = max(1, Int(Double(image.width) * factor)), height = max(1, Int(Double(image.height) * factor))
        var rgba = [UInt8](repeating: 0, count: width * height * 4)
        let ok = rgba.withUnsafeMutableBytes { raw -> Bool in
            guard let context = CGContext(data: raw.baseAddress, width: width, height: height, bitsPerComponent: 8, bytesPerRow: width * 4,
                space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGBitmapInfo.byteOrder32Big.rawValue | CGImageAlphaInfo.premultipliedLast.rawValue) else { return false }
            context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height)); return true
        }
        XCTAssertTrue(ok)
        func centers(red: Bool) -> [CGPoint] {
            var mask = [Bool](repeating: false, count: width * height)
            for index in mask.indices {
                let i = index * 4
                mask[index] = red ? (rgba[i] > 160 && rgba[i + 1] < 100 && rgba[i + 2] < 100)
                    : (rgba[i] < 100 && rgba[i + 1] > 160 && rgba[i + 2] > 160)
            }
            var result: [CGPoint] = []
            for start in mask.indices where mask[start] {
                mask[start] = false
                var pixels = [start], cursor = 0, sumX = 0, sumY = 0
                while cursor < pixels.count {
                    let index = pixels[cursor], x = index % width, y = index / width
                    cursor += 1; sumX += x; sumY += y
                    for dy in -1...1 { for dx in -1...1 {
                        let nx = x + dx, ny = y + dy
                        if nx >= 0 && nx < width && ny >= 0 && ny < height {
                            let next = ny * width + nx
                            if mask[next] { mask[next] = false; pixels.append(next) }
                        }
                    } }
                }
                if !pixels.isEmpty {
                    result.append(CGPoint(x: Double(sumX) / Double(pixels.count), y: Double(sumY) / Double(pixels.count)))
                }
            }
            return result
        }
        let red = centers(red: true), cyan = centers(red: false)
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "main-ground-alignment-\(name)"; attachment.lifetime = .keepAlways; add(attachment)
        XCTAssertEqual(red.count, 3, "Foreground calibration points missing: \(name)")
        XCTAssertEqual(cyan.count, 3, "Receiver calibration points missing: \(name)")
        for point in red {
            let error = cyan.map { hypot(point.x - $0.x, point.y - $0.y) }.min() ?? 1000
            print("ALIGNMENT_ERROR", name, error)
            XCTAssertLessThan(error, 1.5, "Foreground/receiver drift in actual screen pixels: \(name)")
        }
    }

    func testMapContourRendererAndInteraction() {
        continueAfterFailure = false
        XCUIDevice.shared.orientation = .landscapeLeft
        let app = XCUIApplication()
        app.launchArguments = ["-visualReview"]
        app.launch()
        let map = app.otherElements["meadowMap"]
        XCTAssertTrue(map.waitForExistence(timeout: 120))
        waitForReady(app, map: map)
        let state = diagnostics(app)
        XCTAssertGreaterThan(state["shadowFrames"] as? Int ?? 0, 0)
        XCTAssertEqual(state["shadowRenderer"] as? String, "image-alpha relief Metal depth map")
        let startup = state["startup"] as? [String: Double] ?? [:]
        print("STARTUP_METRICS", startup)
        XCTAssertGreaterThan(startup["heartbeats"] ?? 0, 0)
        XCTAssertLessThan(startup["mainThreadLongestGap"] ?? 100, 2.0, "Loading must leave UIKit responsive")
        assertVisibleGround(map, name: "main-ground-visible")
        let play = app.buttons["playButton"]
        play.tap(); XCTAssertEqual(play.label, "暂停行旅")
        app.buttons["zoomButton"].tap()
        XCTAssertEqual(app.buttons["zoomButton"].value as? String, "125%")
        assertVisibleGround(map, name: "main-ground-zoom")
        app.buttons["zoomButton"].tap()
        app.buttons["zoomButton"].tap()
        map.pinch(withScale: 1.3, velocity: 1)
        XCTAssertGreaterThanOrEqual(diagnostics(app)["zoom"] as? Double ?? 0, 1.79)
        assertVisibleGround(map, name: "main-ground-real-map-max-zoom")
        app.buttons["resetButton"].tap()
        XCTAssertEqual(play.label, "开始行旅")
        XCTAssertEqual(app.buttons["zoomButton"].value as? String, "100%")
        app.buttons["openShadowLab"].tap()
        XCTAssertTrue(app.otherElements["shadowLabSurface"].waitForExistence(timeout: 15))
        XCTAssertFalse(app.buttons["shadowLabCasterMode"].exists)
        app.buttons["shadowLabClose"].tap()
        XCTAssertTrue(map.waitForExistence(timeout: 15))
        assertVisibleGround(map, name: "main-ground-return")
    }

    func testShadowLabControlsAndLayout() {
        continueAfterFailure = false
        XCUIDevice.shared.orientation = .landscapeLeft
        let app = XCUIApplication()
        app.launchArguments = ["-shadowReview"]
        app.launch()
        let surface = app.otherElements["shadowLabSurface"]
        XCTAssertTrue(surface.waitForExistence(timeout: 15))
        expectation(for: NSPredicate(format: "value CONTAINS %@", "\"ready\":true"), evaluatedWith: surface)
        waitForExpectations(timeout: 15)
        XCTAssertGreaterThan(surface.frame.width, surface.frame.height)
        capture("08-shadow-lab-artwork")
        app.buttons["shadowLabPause"].tap()
        app.buttons["shadowLabModels"].tap()
        capture("09-shadow-lab-proxies")
        app.buttons["shadowLabModels"].tap()
        app.buttons["shadowLabShadows"].tap()
        XCTAssertTrue((surface.value as? String ?? "").contains("\"shadows\":false"))
        capture("10-shadow-lab-without-shadows")
        app.buttons["shadowLabShadows"].tap()
        app.buttons["shadowLabRelayout"].tap()
        XCTAssertTrue((surface.value as? String ?? "").contains("\"seed\":8"))
        app.buttons["shadowLabSun"].tap()
        app.sliders["shadowLabSunSlider"].adjust(toNormalizedSliderPosition: 0.8)
        surface.pinch(withScale: 1.2, velocity: 1)
        let data = Data((surface.value as! String).utf8)
        let state = try! JSONSerialization.jsonObject(with: data) as! [String: Any]
        XCTAssertGreaterThan(state["zoom"] as? Double ?? 0, 1)
        XCTAssertEqual(state["automaticSun"] as? Bool, false)
        capture("11-shadow-lab-relayout")
        app.buttons["shadowLabClose"].tap()
        XCTAssertTrue(app.buttons["openShadowLab"].waitForExistence(timeout: 15))
        app.buttons["openShadowLab"].tap()
        XCTAssertTrue(surface.waitForExistence(timeout: 15))
    }

    func testEightDirectionReviewSurvivesInitialViewLayout() {
        continueAfterFailure = false
        XCUIDevice.shared.orientation = .landscapeLeft
        let app = XCUIApplication()
        app.launchArguments = ["-gaitReview"]
        app.launch()
        let map = app.otherElements["meadowMap"]
        let ready = NSPredicate(format: "value BEGINSWITH %@", "步态验收：三位人物")
        expectation(for: ready, evaluatedWith: map)
        waitForExpectations(timeout: 15)
        XCTAssertGreaterThan(map.frame.width, map.frame.height)
        capture("06-eight-direction-review")
        expectation(for: NSPredicate(format: "value ENDSWITH %@", "右下"), evaluatedWith: map)
        waitForExpectations(timeout: 28)
        capture("07-diagonal-walking")
    }

    func testPlaybackResetZoomAndCapture() {
        continueAfterFailure = false
        XCUIDevice.shared.orientation = .landscapeLeft
        let app = XCUIApplication()
        app.launchArguments = ["-visualReview"]
        app.launch()
        let play = app.buttons["playButton"]
        XCTAssertTrue(play.waitForExistence(timeout: 15))
        capture("01-reference-layout")
        XCTAssertEqual(play.label, "开始行旅")
        play.tap()
        XCTAssertEqual(play.label, "暂停行旅")
        // Give the characters enough time to travel a visible distance.
        let traveled = expectation(description: "Visible route movement")
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) { traveled.fulfill() }
        waitForExpectations(timeout: 3)
        capture("02-traveling")
        play.tap()
        XCTAssertEqual(play.label, "开始行旅")
        let zoom = app.buttons["zoomButton"]
        zoom.tap()
        XCTAssertEqual(zoom.value as? String, "125%")
        capture("03-zoomed")
        app.buttons["resetButton"].tap()
        XCTAssertEqual(zoom.value as? String, "100%")
        XCTAssertEqual(play.label, "开始行旅")
        capture("04-reset")
        let metrics = diagnostics(app)
        XCTAssertGreaterThan(metrics["independentProps"] as? Int ?? 0, 140)
        XCTAssertEqual(metrics["roads"] as? Int, 4)
        print("SCENE_METRICS", app.otherElements["meadowMap"].value ?? "missing")

        let heroes = metrics["heroTargets"] as! [[String: Double]]
        tap(app, at: heroes[0])
        tap(app, at: diagnostics(app)["orderPoint"] as! [String: Double])
        XCTAssertEqual(play.label, "暂停行旅")
        XCTAssertEqual(diagnostics(app)["mode"] as? String, "destination")
        let destination = diagnostics(app)["goal"] as! [String: Double]
        play.tap()
        XCTAssertEqual(play.label, "开始行旅")
        play.tap()
        let resumed = diagnostics(app)
        XCTAssertEqual(resumed["mode"] as? String, "destination")
        XCTAssertEqual(resumed["goal"] as! [String: Double], destination)
        capture("05-ordered-journey")
    }

    private func assertVisibleGround(_ map: XCUIElement, name: String) {
        let screenshot = XCUIScreen.main.screenshot()
        guard let image = screenshot.image.cgImage else { return XCTFail("Screen capture unavailable") }
        let factor = min(1.0, 512.0 / Double(max(image.width, image.height)))
        let w = max(1, Int(Double(image.width) * factor)), h = max(1, Int(Double(image.height) * factor))
        var rgba = [UInt8](repeating: 0, count: w * h * 4)
        let rendered = rgba.withUnsafeMutableBytes { raw -> Bool in
            guard let context = CGContext(data: raw.baseAddress, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w * 4,
                space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGBitmapInfo.byteOrder32Big.rawValue | CGImageAlphaInfo.premultipliedLast.rawValue) else { return false }
            context.draw(image, in: CGRect(x: 0, y: 0, width: w, height: h)); return true
        }
        XCTAssertTrue(rendered)
        let screen = screenshot.image.size
        let rect = map.frame.insetBy(dx: map.frame.width * 0.08, dy: map.frame.height * 0.15)
        var visible = 0, total = 0
        for row in 0..<40 { for column in 0..<60 {
            let x = min(w - 1, max(0, Int((rect.minX + rect.width * (CGFloat(column) + 0.5) / 60) * CGFloat(w) / screen.width)))
            let y = min(h - 1, max(0, Int((rect.minY + rect.height * (CGFloat(row) + 0.5) / 40) * CGFloat(h) / screen.height)))
            let offset = (y * w + x) * 4
            if max(rgba[offset], max(rgba[offset + 1], rgba[offset + 2])) > 30 { visible += 1 }
            total += 1
        } }
        XCTAssertGreaterThan(Double(visible) / Double(total), 0.75, "Black terrain regression in the actual composited screen: \(name)")
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = name; attachment.lifetime = .keepAlways; add(attachment)
    }

    private func capture(_ name: String) {
        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    private func diagnostics(_ app: XCUIApplication) -> [String: Any] {
        let text = app.otherElements["meadowMap"].value as! String
        return try! JSONSerialization.jsonObject(with: Data(text.utf8)) as! [String: Any]
    }

    private func tap(_ app: XCUIApplication, at point: [String: Double]) {
        app.otherElements["meadowMap"].coordinate(withNormalizedOffset:
            CGVector(dx: point["x"]!, dy: point["y"]!)).tap()
    }
}
