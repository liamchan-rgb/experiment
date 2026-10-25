import UIKit
import SpriteKit
import MetalKit

final class GameViewController: UIViewController, UIGestureRecognizerDelegate {
    private let gameView = UIView()
    private var gaitView: SKView?
    private let scene = GameScene()
    private let loadingView = MeadowLoadingView()
    private var loadStarted = false
    private var ready = false
    private var groundBecameReady = false
    private var foregroundBecameReady = false
    private var loadingTimer: Timer?
    private var loadingBegan: TimeInterval = 0
    private var lastHeartbeat: TimeInterval = 0
    private var longestHeartbeatGap: TimeInterval = 0
    private var loadingHeartbeats = 0
    private var loadingStage = "准备进入林地"
    private var loadingProgress: Float = 0
    private var firstFrameWaitSeconds: TimeInterval?
    private var loadingFailed = false
    private var setupTimings: [String: Double] = [:]
    private var mapPresentationBegan: TimeInterval = 0
    private var groundView: MTKView?
    private var groundRenderer: MeadowShadowRenderer?
    private var gpuProbe: MeadowGPUProbe?
    private var checkedSavedReport = false
    private var mapPresented = false
    private let groundDrawableScale: CGFloat = 1
    private let gpuFallbackCount = 0
    private let titleButton = ParchmentButton(symbol: .title)
    private let playButton = ParchmentButton(symbol: .play)
    private let resetButton = ParchmentButton(symbol: .reset)
    private let zoomButton = ParchmentButton(symbol: .zoom)
    private let shadowLabButton = UIButton(type: .system)
    private let gaitTestButton = UIButton(type: .system)
    private let battlePreviewButton = UIButton(type: .system)
    private var battlePreviewView: MeadowBattlePreviewView?
    private var battlePreviewActive = false
    private var metricsHiddenBeforeBattlePreview = true
    private let gaitPanel = UIStackView()
    private let gaitStatusLabel = UILabel()
    private let gaitPauseButton = UIButton(type: .system)
    private let gaitSlowButton = UIButton(type: .system)
    private let gaitStepButton = UIButton(type: .system)
    private let gaitLayeredPreviewButton = UIButton(type: .system)
    private let p1AppearanceButton = UIButton(type: .system)
    private var gaitDirectionButtons: [UIButton] = []
    private var gaitCaptureTimer: Timer?
    private var gestureZoom: CGFloat = 1
    private let metricsLabel = UILabel()
    private let discoveryLabel = UILabel()
    private let reviewMode = ProcessInfo.processInfo.arguments.contains("-visualReview")

    override var prefersStatusBarHidden: Bool { true }
    override var prefersHomeIndicatorAutoHidden: Bool { true }
    override var supportedInterfaceOrientations: UIInterfaceOrientationMask { .landscape }

    override func loadView() { view = UIView() }

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = UIColor(red: 0.055, green: 0.09, blue: 0.065, alpha: 1)
        gameView.frame = view.bounds
        // This transparent UIView owns gestures/accessibility, not a renderer.
        // Normal map graphics are presented by the single MTKView below it.
        gameView.isOpaque = false
        gameView.backgroundColor = .clear
        view.addSubview(gameView)
        scene.onForegroundReady = { [weak self] in
            guard let self else { return }
            self.setupTimings["mapFirstForegroundDelay"] = ProcessInfo.processInfo.systemUptime - self.mapPresentationBegan
            self.foregroundBecameReady = true; self.finishLoading()
        }
        if !ProcessInfo.processInfo.arguments.contains("-gaitReview"), let device = MTLCreateSystemDefaultDevice() {
            let ground = MTKView(frame: view.bounds, device: device)
            ground.preferredFramesPerSecond = 60
            ground.autoResizeDrawable = true
            ground.colorPixelFormat = .bgra8Unorm
            ground.isOpaque = true
            ground.clearColor = MTLClearColor(red: 0.15, green: 0.20, blue: 0.08, alpha: 1)
            ground.isPaused = true
            ground.isUserInteractionEnabled = false
            ground.accessibilityElementsHidden = true
            view.insertSubview(ground, belowSubview: gameView)
            groundView = ground
            scene.onWorldReady = { [weak self] world in
                guard let self else { return }
                if self.groundRenderer != nil {
                    world.terrain.removeFromParent()
                    self.scene.backgroundColor = .clear
                }
            }
        }
        gameView.isMultipleTouchEnabled = true
        gameView.accessibilityIdentifier = "meadowMap"
        gameView.isAccessibilityElement = true
        gameView.accessibilityLabel = "林间地图，已选择 P1"
        gameView.accessibilityTraits = .allowsDirectInteraction
        scene.scaleMode = .resizeFill
        scene.size = view.bounds.size
        for button in [titleButton, playButton, resetButton, zoomButton] { view.addSubview(button) }
        var labStyle = UIButton.Configuration.filled()
        labStyle.title = "光影试验"
        labStyle.baseBackgroundColor = UIColor(red: 0.97, green: 0.91, blue: 0.70, alpha: 0.96)
        labStyle.baseForegroundColor = UIColor(red: 0.25, green: 0.28, blue: 0.14, alpha: 1)
        shadowLabButton.configuration = labStyle
        shadowLabButton.accessibilityIdentifier = "openShadowLab"
        shadowLabButton.addTarget(self, action: #selector(openShadowLab), for: .touchUpInside)
        view.addSubview(shadowLabButton)
        configureGaitControls()
        configureBattlePreview()
        for label in [metricsLabel, discoveryLabel] {
            label.textColor = UIColor(red: 1, green: 0.94, blue: 0.75, alpha: 1)
            label.backgroundColor = UIColor(red: 0.17, green: 0.22, blue: 0.17, alpha: 0.82)
            label.font = .monospacedDigitSystemFont(ofSize: 12, weight: .medium)
            label.textAlignment = .center
            label.layer.cornerRadius = 6
            label.clipsToBounds = true
            label.isUserInteractionEnabled = false
            view.addSubview(label)
        }
        metricsLabel.numberOfLines = 2
        metricsLabel.isHidden = true
        discoveryLabel.alpha = 0
        titleButton.accessibilityIdentifier = "helpButton"
        titleButton.accessibilityLabel = "安然，查看操作说明"
        titleButton.addTarget(self, action: #selector(showHelp), for: .touchUpInside)
        playButton.accessibilityIdentifier = "playButton"
        playButton.accessibilityLabel = "开始行旅"
        playButton.addTarget(self, action: #selector(togglePlayback), for: .touchUpInside)
        resetButton.accessibilityIdentifier = "resetButton"
        resetButton.accessibilityLabel = "复位地图和人物"
        resetButton.addTarget(self, action: #selector(reset), for: .touchUpInside)
        zoomButton.accessibilityIdentifier = "zoomButton"
        zoomButton.accessibilityLabel = "放大地图"
        zoomButton.accessibilityValue = "100%"
        zoomButton.addTarget(self, action: #selector(zoom), for: .touchUpInside)
        scene.onPlaybackChanged = { [weak self] playing in
            DispatchQueue.main.async {
                self?.playButton.isPlaying = playing
                self?.playButton.accessibilityLabel = playing ? "暂停行旅" : "开始行旅"
            }
        }
        scene.onSelectionChanged = { [weak self] name in
            DispatchQueue.main.async { self?.gameView.accessibilityLabel = "林间地图，已选择 \(name)" }
        }
        scene.onDiagnostics = { [weak self] text in
            guard let self else { return }
            let playing = self.scene.isRunning, zoom = self.scene.zoom
            DispatchQueue.main.async {
                guard !self.loadingFailed else { return }
                self.gameView.accessibilityValue = self.reviewMode ? text : (playing ? "旅人移动中" : "旅人暂停")
                self.zoomButton.accessibilityValue = "\(Int(round(zoom * 100)))%"
            }
        }
        scene.onMetrics = { [weak self] text in DispatchQueue.main.async { self?.metricsLabel.text = text } }
        scene.onDiscovery = { [weak self] text in
            DispatchQueue.main.async {
            guard let self else { return }
            self.discoveryLabel.text = text
            self.discoveryLabel.layer.removeAllAnimations()
            self.discoveryLabel.alpha = 1
            UIView.animate(withDuration: 0.6, delay: 2.2, options: [.beginFromCurrentState]) {
                self.discoveryLabel.alpha = 0
            }
            }
        }
        if ProcessInfo.processInfo.arguments.contains("-gaitReview") {
            let review = GaitReviewScene(size: view.bounds.size)
            review.onReviewAccessibilityValue = { [weak self] value in
                DispatchQueue.main.async { self?.gameView.accessibilityValue = value }
            }
            review.scaleMode = .resizeFill
            let reviewView = SKView(frame: gameView.bounds)
            reviewView.preferredFramesPerSecond = 60
            reviewView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
            gameView.addSubview(reviewView); gaitView = reviewView
            reviewView.presentScene(review)
            mapPresented = true
            for button in [titleButton, playButton, resetButton, zoomButton] { button.isHidden = true }
            shadowLabButton.isHidden = true
            gaitTestButton.isHidden = true
        } else {
            loadingView.frame = view.bounds
            view.addSubview(loadingView)
            loadingView.onRetry = { [weak self] in
                guard let self else { return }
                if !self.loadStarted { self.beginLoading() }
                else if !MeadowGPUDiagnostics.shared.requiresColdLaunch { self.view.window?.rootViewController = GameViewController() }
            }
            loadingView.onCopy = { UIPasteboard.general.string = MeadowGPUDiagnostics.shared.json }
            setMapEnabled(false)
        }
        titleButton.addGestureRecognizer(UILongPressGestureRecognizer(target: self, action: #selector(toggleMetrics(_:))))
        gameView.addGestureRecognizer(UITapGestureRecognizer(target: self, action: #selector(tapMap(_:))))
        let pinch = UIPinchGestureRecognizer(target: self, action: #selector(pinchMap(_:)))
        pinch.delegate = self
        gameView.addGestureRecognizer(pinch)
        let pan = UIPanGestureRecognizer(target: self, action: #selector(panMap(_:)))
        pan.minimumNumberOfTouches = 2
        pan.maximumNumberOfTouches = 2
        pan.delegate = self
        gameView.addGestureRecognizer(pan)
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        let mapFrame: CGRect
        if battlePreviewActive, let preview = battlePreviewView {
            preview.frame = view.bounds
            mapFrame = preview.mapFrame
        } else {
            battlePreviewView?.frame = .zero
            mapFrame = view.bounds
        }
        let mapWidth = mapFrame.width
        gameView.frame = mapFrame
        groundView?.frame = mapFrame
        groundView?.layer.cornerRadius = battlePreviewActive ? 14 : 0
        groundView?.clipsToBounds = battlePreviewActive
        scene.resizeMapViewport(to: mapFrame.size, referenceSize: view.bounds.size)
        loadingView.frame = view.bounds
        let inset = view.safeAreaInsets
        let top = max(inset.top, 6)
        let isPad = traitCollection.userInterfaceIdiom == .pad
        let button: CGFloat = isPad ? 44 : 34
        let spacing = button + 2
        titleButton.frame = CGRect(x: max(inset.left, 10) + 4, y: top, width: isPad ? 88 : 70, height: isPad ? 44 : 38)
        shadowLabButton.frame = CGRect(x: titleButton.frame.maxX + 8, y: top + 2, width: 96, height: button)
        gaitTestButton.frame = CGRect(x: (scene.gaitTest == nil ? shadowLabButton.frame.maxX : titleButton.frame.maxX) + 8,
                                      y: top + 2, width: 100, height: button)
        let battleX = battlePreviewActive ? titleButton.frame.maxX + 8 : gaitTestButton.frame.maxX + 8
        battlePreviewButton.frame = CGRect(x: battleX, y: top + 2, width: 104, height: button)
        p1AppearanceButton.frame = CGRect(x: battlePreviewButton.frame.maxX + 8, y: top + 2, width: 112, height: button)
        let panelWidth = min(960, max(1, mapWidth - 32))
        gaitPanel.frame = CGRect(x: (view.bounds.width - panelWidth) / 2,
                                 y: view.bounds.height - max(inset.bottom, 12) - 194, width: panelWidth, height: 194)
        let right = mapWidth - max(inset.right, 10) - 4
        zoomButton.frame = CGRect(x: right - button, y: top + 2, width: button, height: button)
        resetButton.frame = zoomButton.frame.offsetBy(dx: -spacing, dy: 0)
        playButton.frame = resetButton.frame.offsetBy(dx: -spacing, dy: 0)
        if scene.gaitTest == nil && p1AppearanceButton.frame.maxX > playButton.frame.minX - 8 {
            p1AppearanceButton.frame.origin = CGPoint(x: titleButton.frame.minX, y: top + button + 10)
        }
        metricsLabel.frame = CGRect(x: right - 225, y: view.bounds.height - max(inset.bottom, 10) - 50, width: 225, height: 48)
        discoveryLabel.frame = CGRect(x: view.bounds.midX - 110, y: view.bounds.height - max(inset.bottom, 10) - 44, width: 220, height: 34)
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        if !ProcessInfo.processInfo.arguments.contains("-gaitReview") { beginLoading() }
    }

    private func beginLoading() {
        guard !loadStarted else { return }
        if !checkedSavedReport {
            checkedSavedReport = true
            if MeadowGPUDiagnostics.shared.recordedBuild == Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String,
               let saved = MeadowGPUDiagnostics.shared.savedFailureOrInterruption {
                loadingView.showSavedReport(saved)
                return
            }
        }
        loadStarted = true
        guard groundView?.device != nil else { showLoadingFailure(ShadowLabError.setup("无法取得 Metal 设备")); return }
        MeadowGPUDiagnostics.shared.begin(device: groundView?.device, size: gameView.bounds.size, scale: gameView.contentScaleFactor)
        MeadowGPUDiagnostics.shared.beginStage("资源准备", kind: "CPU setup; not GPU fault attribution")
        loadingBegan = ProcessInfo.processInfo.systemUptime
        lastHeartbeat = loadingBegan
        longestHeartbeatGap = 0; loadingHeartbeats = 0
        loadingTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            guard let self else { return }
            let now = ProcessInfo.processInfo.systemUptime
            self.longestHeartbeatGap = max(self.longestHeartbeatGap, now - self.lastHeartbeat)
            if let waited = self.firstFrameWaitSeconds, UIApplication.shared.applicationState == .active {
                // Count active heartbeat time; app suspension must not consume
                // the first-frame timeout when the user returns to loading.
                let elapsed = waited + min(now - self.lastHeartbeat, 1)
                self.firstFrameWaitSeconds = elapsed
                if elapsed >= 20 {
                    self.failRendering(ShadowLabError.setup("首帧渲染等待超时，请重新加载"))
                }
            }
            self.lastHeartbeat = now; self.loadingHeartbeats += 1
        }
        MeadowLoader.load(device: groundView?.device, diagnosticSize: gameView.bounds.size, progress: { [weak self] value, text in
            self?.reportLoadingProgress(value, text: text)
        }) { [weak self] result in
            guard let self, !self.loadingFailed else { return }
            switch result {
            case .success(let prepared):
                self.groundRenderer = prepared.renderer
                self.scene.shadowMapSize = prepared.renderer?.shadowSize ?? 0
                self.groundRenderer?.alignmentReview = ProcessInfo.processInfo.arguments.contains("-alignmentReview")
                self.groundRenderer?.onFirstFrameCompleted = { [weak self] in
                    self?.groundBecameReady = true
                    self?.foregroundBecameReady = true // Same completed command includes the foreground.
                    self?.finishLoading()
                }
                self.groundRenderer?.onFrameFailed = { [weak self] error in self?.failRendering(error) }
                do {
                    MeadowGPUDiagnostics.shared.beginStage("B00 前景诊断目标准备", kind: "CPU SKRenderer setup; not GPU completion")
                    let probe = try MeadowGPUProbe(prepared: prepared, size: self.gameView.bounds.size,
                        scale: self.gameView.contentScaleFactor, progress: { [weak self] value, label in
                            self?.reportLoadingProgress(Float(0.84 + value * 0.12), text: label)
                        })
                    self.gpuProbe = probe
                    probe.start { [weak self] result in
                        guard let self else { return }
                        self.gpuProbe = nil
                        switch result {
                        case .success: self.prepareWorld(prepared)
                        case .failure(let error): self.showLoadingFailure(error)
                        }
                    }
                } catch {
                    self.showLoadingFailure(error)
                }
            case .failure(let error): self.showLoadingFailure(error)
            }
        }
    }

    private func prepareWorld(_ prepared: PreparedMeadow) {
        reportLoadingProgress(0.96, text: "布置场景")
        scene.size = gameView.bounds.size
        scene.prepare(prepared, progress: { [weak self] value in
            self?.reportLoadingProgress(Float(0.96 + value * 0.03), text: "布置场景")
        }) { [weak self] in
            guard let self, !self.loadingFailed else { return }
            self.reportLoadingProgress(0.99, text: "显示林地")
            // Only the actual map's first frame gets a timeout. Shader warmup
            // and world population may take longer on slower physical iPads.
            self.firstFrameWaitSeconds = 0
            self.mapPresentationBegan = ProcessInfo.processInfo.systemUptime
            guard let surface = self.groundView, let renderer = self.groundRenderer else {
                self.showLoadingFailure(ShadowLabError.setup("单视图地图渲染器缺失")); return
            }
            MeadowGPUDiagnostics.shared.beginStage("C02 实际单视图地图", kind: "one MTKView; native backdrop + SKRenderer in one submitted command buffer")
            self.scene.activateForMetalRenderer()
            self.mapPresented = true
            renderer.start(in: surface, scene: self.scene)
            self.setupTimings["presentMap"] = ProcessInfo.processInfo.systemUptime - self.mapPresentationBegan
        }
    }

    private func reportLoadingProgress(_ value: Float, text: String) {
        guard !ready, !loadingFailed else { return }
        loadingProgress = max(loadingProgress, min(1, value))
        loadingStage = text
        loadingView.update(value, text: text)
        if reviewMode { gameView.accessibilityValue = "{\"loadingProgress\":\(loadingProgress),\"phase\":\"\(text)\"}" }
    }

    private func finishLoading() {
        guard !ready, !loadingFailed, foregroundBecameReady, groundRenderer == nil || groundBecameReady else { return }
        ready = true
        firstFrameWaitSeconds = nil
        let now = ProcessInfo.processInfo.systemUptime
        loadingTimer?.invalidate(); loadingTimer = nil
        scene.startupMetrics = ["seconds": now - loadingBegan,
            "mainThreadLongestGap": max(longestHeartbeatGap, now - lastHeartbeat), "heartbeats": Double(loadingHeartbeats)]
            .merging(setupTimings, uniquingKeysWith: { _, new in new })
            .merging(scene.setupTimings, uniquingKeysWith: { _, new in new })
        scene.shadowReady = groundRenderer?.shadowsEnabled ?? false
        scene.shadowMapSize = groundRenderer?.shadowSize ?? 0
        scene.gpuFallbackCount = gpuFallbackCount
        scene.groundDrawableScale = Double(groundDrawableScale)
        scene.refreshDiagnostics()
        MeadowGPUDiagnostics.shared.mapReady()
        loadingView.update(1, text: "准备就绪")
        loadingView.isHidden = true
        setMapEnabled(true)
        if ProcessInfo.processInfo.arguments.contains("-gaitCapture") { startGaitCapture() }
    }

    /// CI records the real single-MTKView renderer, at normal and quarter speed.
    /// This deliberately uses the same scene and controls as manual inspection.
    private func startGaitCapture() {
        scene.toggleGaitTest()
        let slow = ProcessInfo.processInfo.arguments.contains("-slowGaitCapture")
        if slow { scene.toggleGaitSlow() }
        let order = GaitTest.menuOrder
        scene.setGaitDirection(order[0]); refreshGaitControls()
        let directory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        try? Data("ready".utf8).write(to: directory.appendingPathComponent("GaitCaptureReady.txt"), options: .atomic)
        var index = 0
        gaitCaptureTimer = Timer.scheduledTimer(withTimeInterval: slow ? 6 : 4, repeats: true) { [weak self] _ in
            index = (index + 1) % order.count
            self?.scene.setGaitDirection(order[index]); self?.refreshGaitControls()
        }
    }

    private func setMapEnabled(_ enabled: Bool) {
        gameView.isUserInteractionEnabled = enabled
        for button in [titleButton, playButton, resetButton, zoomButton] { button.isEnabled = enabled }
        shadowLabButton.isEnabled = enabled
        gaitTestButton.isEnabled = enabled
        battlePreviewButton.isEnabled = enabled
        p1AppearanceButton.isEnabled = enabled
        gaitPanel.isUserInteractionEnabled = enabled
    }

    private func failRendering(_ error: Error) { showLoadingFailure(error) }

    private func showLoadingFailure(_ error: Error) {
        guard !loadingFailed else { return }
        let first = MeadowGPUDiagnostics.shared.failed(error)
        loadingFailed = true; firstFrameWaitSeconds = nil
        loadingTimer?.invalidate(); loadingTimer = nil
        setRenderingPaused(true)
        setMapEnabled(false)
        loadingView.isHidden = false
        loadingView.failed(first, restartRequired: MeadowGPUDiagnostics.shared.requiresColdLaunch)
        if reviewMode, let data = try? JSONSerialization.data(withJSONObject: [
            "loadingError": error.localizedDescription, "loadingProgress": loadingProgress,
            "loadingStage": loadingStage,
            "foregroundReady": foregroundBecameReady, "groundReady": groundBecameReady,
            "shadowFrames": groundRenderer?.submittedFrames ?? 0,
            "gpuFallbackCount": gpuFallbackCount,
            "shadowMapSize": groundRenderer?.shadowSize ?? 0,
            "shadowsEnabled": groundRenderer?.shadowsEnabled ?? false,
            "groundDrawableScale": groundDrawableScale
        ]), let text = String(data: data, encoding: .utf8) { gameView.accessibilityValue = text }
    }

    @objc private func togglePlayback() { scene.togglePlayback() }

    private func configureGaitControls() {
        var style = UIButton.Configuration.filled()
        style.baseBackgroundColor = UIColor(red: 0.97, green: 0.91, blue: 0.70, alpha: 0.96)
        style.baseForegroundColor = UIColor(red: 0.25, green: 0.28, blue: 0.14, alpha: 1)
        style.contentInsets = NSDirectionalEdgeInsets(top: 6, leading: 4, bottom: 6, trailing: 4)
        gaitTestButton.configuration = style
        gaitTestButton.configuration?.title = "步态测试"
        gaitTestButton.accessibilityIdentifier = "openGaitTest"
        gaitTestButton.addAction(UIAction { [weak self] _ in
            self?.scene.toggleGaitTest(); self?.refreshGaitControls()
        }, for: .touchUpInside)
        view.addSubview(gaitTestButton)
        p1AppearanceButton.configuration = style
        p1AppearanceButton.configuration?.title = "P1 衣装"
        p1AppearanceButton.accessibilityIdentifier = "p1Appearance"
        p1AppearanceButton.accessibilityValue = HeroFrames.appearanceTitles.first
        p1AppearanceButton.showsMenuAsPrimaryAction = true
        p1AppearanceButton.menu = UIMenu(children: HeroFrames.appearanceTitles.enumerated().map { index, title in
            UIAction(title: title) { [weak self] _ in
                guard let self else { return }
                self.scene.selectP1Appearance(index)
                self.p1AppearanceButton.configuration?.title = title
                self.p1AppearanceButton.accessibilityValue = title
            }
        })
        p1AppearanceButton.isHidden = HeroFrames.appearanceTitles.isEmpty
        view.addSubview(p1AppearanceButton)
        gaitPanel.axis = .vertical; gaitPanel.spacing = 6
        gaitPanel.isLayoutMarginsRelativeArrangement = true
        gaitPanel.layoutMargins = UIEdgeInsets(top: 8, left: 8, bottom: 8, right: 8)
        gaitPanel.backgroundColor = UIColor(red: 0.13, green: 0.18, blue: 0.14, alpha: 0.94)
        gaitPanel.layer.cornerRadius = 10
        gaitPanel.isHidden = true
        gaitStatusLabel.textColor = .white
        gaitStatusLabel.textAlignment = .center
        gaitStatusLabel.font = .systemFont(ofSize: 15, weight: .medium)
        gaitPanel.addArrangedSubview(gaitStatusLabel)
        let directions = UIStackView(); directions.distribution = .fillEqually; directions.spacing = 4
        for facing in GaitTest.menuOrder {
            let button = UIButton(type: .system); button.configuration = style
            button.configuration?.title = GaitTest.names[facing]
            button.tag = facing
            button.accessibilityIdentifier = "gaitDirection\(facing)"
            button.addAction(UIAction { [weak self] _ in
                self?.scene.setGaitDirection(facing); self?.refreshGaitControls()
            }, for: .touchUpInside)
            directions.addArrangedSubview(button); gaitDirectionButtons.append(button)
        }
        directions.heightAnchor.constraint(equalToConstant: 44).isActive = true
        gaitPanel.addArrangedSubview(directions)
        let controls = UIStackView(); controls.distribution = .fillEqually; controls.spacing = 6
        let restart = UIButton(type: .system)
        for button in [gaitPauseButton, gaitSlowButton, gaitStepButton, restart] {
            button.configuration = style; controls.addArrangedSubview(button)
        }
        gaitStepButton.configuration?.title = "单步"
        gaitStepButton.accessibilityIdentifier = "gaitStep"
        gaitPauseButton.accessibilityIdentifier = "gaitPause"
        gaitSlowButton.accessibilityIdentifier = "gaitSlow"
        restart.configuration?.title = "重新走"
        gaitPauseButton.addAction(UIAction { [weak self] _ in self?.scene.toggleGaitPause(); self?.refreshGaitControls() }, for: .touchUpInside)
        gaitSlowButton.addAction(UIAction { [weak self] _ in self?.scene.toggleGaitSlow(); self?.refreshGaitControls() }, for: .touchUpInside)
        gaitStepButton.addAction(UIAction { [weak self] _ in self?.scene.stepGait(); self?.refreshGaitControls() }, for: .touchUpInside)
        restart.addAction(UIAction { [weak self] _ in self?.scene.reset(); self?.refreshGaitControls() }, for: .touchUpInside)
        controls.heightAnchor.constraint(equalToConstant: 42).isActive = true
        gaitPanel.addArrangedSubview(controls)
        gaitLayeredPreviewButton.configuration = style
        gaitLayeredPreviewButton.configuration?.title = "原图 / 分层蓝靴对照"
        gaitLayeredPreviewButton.accessibilityIdentifier = "gaitLayeredPreview"
        gaitLayeredPreviewButton.heightAnchor.constraint(equalToConstant: 38).isActive = true
        gaitLayeredPreviewButton.addAction(UIAction { [weak self] _ in
            self?.scene.toggleLayeredPreview(); self?.refreshGaitControls()
        }, for: .touchUpInside)
        if HeroFrames.layeredPrototypeAvailable {
            gaitPanel.addArrangedSubview(gaitLayeredPreviewButton)
        }
        view.addSubview(gaitPanel)
    }

    private func configureBattlePreview() {
        var style = UIButton.Configuration.filled()
        style.title = "林地战斗"
        style.baseBackgroundColor = UIColor(red: 0.97, green: 0.91, blue: 0.70, alpha: 0.96)
        style.baseForegroundColor = UIColor(red: 0.25, green: 0.28, blue: 0.14, alpha: 1)
        style.contentInsets = NSDirectionalEdgeInsets(top: 6, leading: 6, bottom: 6, trailing: 6)
        battlePreviewButton.configuration = style
        battlePreviewButton.accessibilityIdentifier = "openBattlePreview"
        battlePreviewButton.accessibilityLabel = "打开 Meadow Journey 可交互林地战斗"
        battlePreviewButton.addAction(UIAction { [weak self] _ in
            guard let self else { return }
            self.setBattlePreviewActive(!self.battlePreviewActive)
        }, for: .touchUpInside)
        view.addSubview(battlePreviewButton)

        let preview = MeadowBattlePreviewView(frame: .zero)
        preview.isHidden = true
        preview.onPartyActiveChanged={ [weak self] active in
            guard let self else { return };self.groundView?.isPaused=active || !self.mapPresented || self.loadingFailed
        }
        preview.onClose = { [weak self] in self?.setBattlePreviewActive(false) }
        preview.onLayoutChanged = { [weak self] in
            guard let self else { return }
            self.view.setNeedsLayout(); self.view.layoutIfNeeded()
        }
        view.addSubview(preview)
        battlePreviewView = preview
    }

    private func setBattlePreviewActive(_ active: Bool) {
        guard active != battlePreviewActive else { return }
        guard scene.gaitTest == nil else { return }
        p1AppearanceButton.isHidden = active || HeroFrames.appearanceTitles.isEmpty
        if active { metricsHiddenBeforeBattlePreview = metricsLabel.isHidden }
        if active { scene.beginBattlePreviewCamera() }
        battlePreviewActive = active
        battlePreviewView?.isHidden = !active
        battlePreviewView?.setActive(active)
        battlePreviewButton.isHidden = active
        shadowLabButton.isHidden = active
        gaitTestButton.isHidden = active
        for control in [titleButton, playButton, resetButton, zoomButton] { control.isHidden = active }
        metricsLabel.isHidden = active ? true : metricsHiddenBeforeBattlePreview
        discoveryLabel.isHidden = active
        if active { gameView.accessibilityLabel = "Meadow Journey 林间地图，显示在左侧；右侧为可交互林地战斗" }
        else { gameView.accessibilityLabel = "林间地图，已选择 P1" }
        view.setNeedsLayout()
        view.layoutIfNeeded()
        if !active {
            scene.endBattlePreviewCamera()
            zoomButton.accessibilityValue = "\(Int(round(scene.zoom * 100)))%"
        }
    }

    private func refreshGaitControls() {
        let active = scene.gaitTest != nil
        gaitPanel.isHidden = !active
        gaitTestButton.configuration?.title = active ? "返回地图" : "步态测试"
        battlePreviewButton.isHidden = active || battlePreviewActive
        let mapControls: [UIView] = [shadowLabButton, playButton, resetButton, zoomButton]
        for control in mapControls { control.isHidden = active }
        if let test = scene.gaitTest {
            gaitStatusLabel.text = scene.layeredPreview
                ? "P1 原图 / 分层蓝靴 · 同步向下循环 · " + (test.slow ? "四分之一速度" : "正常速度")
                : "P1 / P2 / P3 · " + GaitTest.names[test.facing] + " · 直线循环（走完回起点） · " + (test.slow ? "四分之一速度" : "正常速度")
            gaitPauseButton.configuration?.title = test.paused ? "继续" : "暂停"
            gaitSlowButton.configuration?.title = test.slow ? "切回正常" : "切换慢速"
            for button in gaitDirectionButtons {
                button.configuration?.baseBackgroundColor = button.tag == test.facing
                    ? UIColor(red: 0.98, green: 0.72, blue: 0.24, alpha: 1)
                    : UIColor(red: 0.97, green: 0.91, blue: 0.70, alpha: 0.96)
            }
        }
        gaitLayeredPreviewButton.configuration?.title = scene.layeredPreview ? "退出分层对照" : "原图 / 分层蓝靴对照"
        for button in gaitDirectionButtons { button.isEnabled = !scene.layeredPreview }
        view.setNeedsLayout()
    }

    @objc private func openShadowLab() {
        let lab = ShadowLabViewController()
        lab.modalPresentationStyle = .fullScreen
        present(lab, animated: true)
    }

    private func setRenderingPaused(_ paused: Bool) { groundView?.isPaused = paused; gaitView?.isPaused = paused }
    override func viewWillAppear(_ animated: Bool) { super.viewWillAppear(animated); setRenderingPaused(!mapPresented || loadingFailed) }
    override func viewDidDisappear(_ animated: Bool) { super.viewDidDisappear(animated); setRenderingPaused(true) }

    @objc private func tapMap(_ recognizer: UITapGestureRecognizer) { scene.handleTap(inView: recognizer.location(in: gameView)) }

    @objc private func reset() {
        scene.reset()
        zoomButton.accessibilityValue = "100%"
    }

    @objc private func zoom() {
        scene.setZoom(scene.zoom >= 1.79 ? 1 : scene.zoom + 0.25)
        zoomButton.accessibilityValue = "\(Int(scene.zoom * 100))%"
    }

    @objc private func pinchMap(_ recognizer: UIPinchGestureRecognizer) {
        if recognizer.state == .began { gestureZoom = scene.zoom }
        scene.setZoom(gestureZoom * recognizer.scale, anchorInView: recognizer.location(in: gameView))
        zoomButton.accessibilityValue = "\(Int(scene.zoom * 100))%"
    }

    @objc private func panMap(_ recognizer: UIPanGestureRecognizer) {
        scene.panBy(recognizer.translation(in: gameView))
        recognizer.setTranslation(.zero, in: gameView)
    }

    func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer,
                           shouldRecognizeSimultaneouslyWith otherGestureRecognizer: UIGestureRecognizer) -> Bool { true }

    @objc private func toggleMetrics(_ recognizer: UILongPressGestureRecognizer) {
        if recognizer.state == .began { metricsLabel.isHidden.toggle() }
    }

    @objc private func showHelp() {
        let help = UIAlertController(title: "安然 · 林间行旅",
                                     message: "▶ 三位旅人沿土路往返；Ⅱ 暂停后保留目的地\n点选 P1 / P2 / P3，再点道路指定目的地\n点问号，让旅人抵达并探索\n↻ 恢复初始位置；＋ 放大\n双指缩放、拖动；长按安然显示运行指标\n战斗预览：地图留在左侧，右侧检查 Meadow Journey 林地横版场景\n步态测试：选择八个方向直线行走，可慢速、暂停和单步；走完一段会回到起点继续", preferredStyle: .alert)
        help.addAction(UIAlertAction(title: "出发", style: .default))
        help.addAction(UIAlertAction(title: "复制 GPU 诊断", style: .default) { _ in
            UIPasteboard.general.string = MeadowGPUDiagnostics.shared.json
        })
        present(help, animated: true)
    }
}
