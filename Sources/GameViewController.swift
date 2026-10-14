import UIKit
import SpriteKit

final class GameViewController: UIViewController, UIGestureRecognizerDelegate {
    private let gameView = SKView()
    private let scene = GameScene()
    private let titleButton = ParchmentButton(symbol: .title)
    private let playButton = ParchmentButton(symbol: .play)
    private let resetButton = ParchmentButton(symbol: .reset)
    private let zoomButton = ParchmentButton(symbol: .zoom)
    private var gestureZoom: CGFloat = 1

    override var prefersStatusBarHidden: Bool { true }
    override var prefersHomeIndicatorAutoHidden: Bool { true }
    override var supportedInterfaceOrientations: UIInterfaceOrientationMask { .landscape }

    override func loadView() { view = UIView() }

    override func viewDidLoad() {
        super.viewDidLoad()
        gameView.frame = view.bounds
        view.addSubview(gameView)
        gameView.ignoresSiblingOrder = true
        gameView.preferredFramesPerSecond = 60
        gameView.isMultipleTouchEnabled = true
        gameView.accessibilityIdentifier = "meadowMap"
        gameView.isAccessibilityElement = true
        gameView.accessibilityLabel = "林间地图，已选择 P1"
        gameView.accessibilityTraits = .allowsDirectInteraction
        scene.scaleMode = .resizeFill
        scene.size = view.bounds.size
        gameView.presentScene(scene)
        for button in [titleButton, playButton, resetButton, zoomButton] { view.addSubview(button) }
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
            self?.playButton.isPlaying = playing
            self?.playButton.accessibilityLabel = playing ? "暂停行旅" : "开始行旅"
        }
        scene.onSelectionChanged = { [weak self] name in
            self?.gameView.accessibilityLabel = "林间地图，已选择 \(name)"
        }
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
        let inset = view.safeAreaInsets
        let top = max(inset.top, 6)
        titleButton.frame = CGRect(x: max(inset.left, 10) + 4, y: top, width: 70, height: 38)
        let right = view.bounds.width - max(inset.right, 10) - 4
        zoomButton.frame = CGRect(x: right - 34, y: top + 2, width: 34, height: 34)
        resetButton.frame = zoomButton.frame.offsetBy(dx: -36, dy: 0)
        playButton.frame = resetButton.frame.offsetBy(dx: -36, dy: 0)
    }

    @objc private func togglePlayback() { scene.togglePlayback() }

    @objc private func reset() {
        scene.reset()
        zoomButton.accessibilityValue = "100%"
    }

    @objc private func zoom() {
        scene.setZoom(scene.zoom >= 1.65 ? 1 : scene.zoom + 0.25)
        zoomButton.accessibilityValue = "\(Int(scene.zoom * 100))%"
    }

    @objc private func pinchMap(_ recognizer: UIPinchGestureRecognizer) {
        if recognizer.state == .began { gestureZoom = scene.zoom }
        scene.setZoom(gestureZoom * recognizer.scale)
        zoomButton.accessibilityValue = "\(Int(scene.zoom * 100))%"
    }

    @objc private func panMap(_ recognizer: UIPanGestureRecognizer) {
        scene.panBy(recognizer.translation(in: gameView))
        recognizer.setTranslation(.zero, in: gameView)
    }

    func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer,
                           shouldRecognizeSimultaneouslyWith otherGestureRecognizer: UIGestureRecognizer) -> Bool { true }

    @objc private func showHelp() {
        let help = UIAlertController(title: "安然 · 林间行旅",
                                     message: "▶ 三位旅人沿土路往返\n点选 P1 / P2 / P3，再点土路指定目的地\n↻ 恢复样例中的初始位置\n＋ 放大地图；双指缩放、拖动\n点问号发现林间微光", preferredStyle: .alert)
        help.addAction(UIAlertAction(title: "出发", style: .default))
        present(help, animated: true)
    }
}
