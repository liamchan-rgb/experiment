import UIKit
import SpriteKit
import MetalKit

final class GameViewController: UIViewController, UIGestureRecognizerDelegate {
    private let gameView = SKView()
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
    private var groundView: MTKView?
    private var groundRenderer: MeadowShadowRenderer?
    private let titleButton = ParchmentButton(symbol: .title)
    private let playButton = ParchmentButton(symbol: .play)
    private let resetButton = ParchmentButton(symbol: .reset)
    private let zoomButton = ParchmentButton(symbol: .zoom)
    private let shadowLabButton = UIButton(type: .system)
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
        gameView.frame = view.bounds
        // Configure the layer before presenting the scene/creating its renderer.
        gameView.isOpaque = false
        gameView.allowsTransparency = true
        gameView.backgroundColor = .clear
        view.addSubview(gameView)
        gameView.ignoresSiblingOrder = true
        scene.onForegroundReady = { [weak self] in self?.foregroundBecameReady = true; self?.finishLoading() }
        if !ProcessInfo.processInfo.arguments.contains("-gaitReview"), let device = MTLCreateSystemDefaultDevice() {
            let ground = MTKView(frame: view.bounds, device: device)
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
            scene.onRenderGround = { [weak self] world, camera, time, heroes in
                guard let self, let surface = self.groundView else { return }
                do {
                    try self.groundRenderer?.render(in: surface, world: world, camera: camera, time: time, heroes: heroes)
                    self.scene.shadowFrames = self.groundRenderer?.submittedFrames ?? 0
                }
                catch { DispatchQueue.main.async { self.failRendering(error) } }
            }
        }
        gameView.preferredFramesPerSecond = 60
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
            review.scaleMode = .resizeFill
            gameView.presentScene(review)
            for button in [titleButton, playButton, resetButton, zoomButton] { button.isHidden = true }
            shadowLabButton.isHidden = true
        } else {
            loadingView.frame = view.bounds
            view.addSubview(loadingView)
            loadingView.onRetry = { [weak self] in self?.view.window?.rootViewController = GameViewController() }
            setMapEnabled(false)
        }
        titleButton.addGestureRecognizer(UILongPressGestureRecognizer(target: self, action: #selector(toggleMetrics(_:))))
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
        gameView.frame = view.bounds
        groundView?.frame = view.bounds
        loadingView.frame = view.bounds
        let inset = view.safeAreaInsets
        let top = max(inset.top, 6)
        let isPad = traitCollection.userInterfaceIdiom == .pad
        let button: CGFloat = isPad ? 44 : 34
        let spacing = button + 2
        titleButton.frame = CGRect(x: max(inset.left, 10) + 4, y: top, width: isPad ? 88 : 70, height: isPad ? 44 : 38)
        shadowLabButton.frame = CGRect(x: titleButton.frame.maxX + 8, y: top + 2, width: 96, height: button)
        let right = view.bounds.width - max(inset.right, 10) - 4
        zoomButton.frame = CGRect(x: right - button, y: top + 2, width: button, height: button)
        resetButton.frame = zoomButton.frame.offsetBy(dx: -spacing, dy: 0)
        playButton.frame = resetButton.frame.offsetBy(dx: -spacing, dy: 0)
        metricsLabel.frame = CGRect(x: right - 225, y: view.bounds.height - max(inset.bottom, 10) - 50, width: 225, height: 48)
        discoveryLabel.frame = CGRect(x: view.bounds.midX - 110, y: view.bounds.height - max(inset.bottom, 10) - 44, width: 220, height: 34)
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        if !ProcessInfo.processInfo.arguments.contains("-gaitReview") { beginLoading() }
    }

    private func beginLoading() {
        guard !loadStarted else { return }
        loadStarted = true
        loadingBegan = ProcessInfo.processInfo.systemUptime
        lastHeartbeat = loadingBegan
        longestHeartbeatGap = 0; loadingHeartbeats = 0
        loadingTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            guard let self else { return }
            let now = ProcessInfo.processInfo.systemUptime
            self.longestHeartbeatGap = max(self.longestHeartbeatGap, now - self.lastHeartbeat)
            self.lastHeartbeat = now; self.loadingHeartbeats += 1
        }
        MeadowLoader.load(device: groundView?.device, progress: { [weak self] value, text in
            self?.loadingView.update(value, text: text)
        }) { [weak self] result in
            guard let self else { return }
            switch result {
            case .success(let prepared):
                self.groundRenderer = prepared.renderer
                self.groundRenderer?.alignmentReview = ProcessInfo.processInfo.arguments.contains("-alignmentReview")
                self.groundRenderer?.onFirstFrameCompleted = { [weak self] in self?.groundBecameReady = true; self?.finishLoading() }
                self.groundRenderer?.onFrameFailed = { [weak self] error in self?.failRendering(error) }
                self.scene.size = self.gameView.bounds.size
                self.scene.prepare(prepared)
                self.loadingView.update(0.98, text: "显示林地")
                self.gameView.presentScene(self.scene)
                if prepared.renderer == nil { self.finishLoading() }
            case .failure(let error): self.loadingTimer?.invalidate(); self.loadingView.failed(error)
            }
        }
    }

    private func finishLoading() {
        guard !ready, foregroundBecameReady, groundRenderer == nil || groundBecameReady else { return }
        ready = true
        let now = ProcessInfo.processInfo.systemUptime
        loadingTimer?.invalidate(); loadingTimer = nil
        scene.startupMetrics = ["seconds": now - loadingBegan,
            "mainThreadLongestGap": max(longestHeartbeatGap, now - lastHeartbeat), "heartbeats": Double(loadingHeartbeats)]
        scene.shadowReady = groundRenderer != nil
        loadingView.update(1, text: "准备就绪")
        loadingView.isHidden = true
        setMapEnabled(true)
    }

    private func setMapEnabled(_ enabled: Bool) {
        gameView.isUserInteractionEnabled = enabled
        for button in [titleButton, playButton, resetButton, zoomButton] { button.isEnabled = enabled }
        shadowLabButton.isEnabled = enabled
    }

    private func failRendering(_ error: Error) {
        loadingTimer?.invalidate(); loadingTimer = nil
        gameView.isPaused = true
        setMapEnabled(false)
        loadingView.isHidden = false
        loadingView.failed(error)
    }

    @objc private func togglePlayback() { scene.togglePlayback() }

    @objc private func openShadowLab() {
        let lab = ShadowLabViewController()
        lab.modalPresentationStyle = .fullScreen
        present(lab, animated: true)
    }

    override func viewWillAppear(_ animated: Bool) { super.viewWillAppear(animated); gameView.isPaused = false }
    override func viewDidDisappear(_ animated: Bool) { super.viewDidDisappear(animated); gameView.isPaused = true }

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
                                     message: "▶ 三位旅人沿土路往返；Ⅱ 暂停后保留目的地\n点选 P1 / P2 / P3，再点道路指定目的地\n点问号，让旅人抵达并探索\n↻ 恢复初始位置；＋ 放大\n双指缩放、拖动；长按安然显示运行指标", preferredStyle: .alert)
        help.addAction(UIAlertAction(title: "出发", style: .default))
        present(help, animated: true)
    }
}
