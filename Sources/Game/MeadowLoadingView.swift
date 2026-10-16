import UIKit

final class MeadowLoadingView: UIView {
    private let title = UILabel()
    private let status = UILabel()
    private let bar = UIProgressView(progressViewStyle: .default)
    private let spinner = UIActivityIndicatorView(style: .medium)
    private let retry = UIButton(type: .system)
    var onRetry: (() -> Void)?

    override init(frame: CGRect) {
        super.init(frame: frame)
        // Keep the first SpriteKit/Metal frames eligible for presentation under
        // the loading page; readiness must not depend on an occluded surface.
        isOpaque = false
        backgroundColor = UIColor(red: 0.10, green: 0.15, blue: 0.10, alpha: 0.99)
        accessibilityIdentifier = "meadowLoading"
        title.text = "林间行旅"
        title.font = .systemFont(ofSize: 25, weight: .semibold)
        title.textColor = UIColor(red: 1, green: 0.94, blue: 0.76, alpha: 1)
        status.font = .monospacedDigitSystemFont(ofSize: 14, weight: .regular)
        status.textColor = title.textColor
        status.accessibilityIdentifier = "loadingStatus"
        for label in [title, status] { label.textAlignment = .center }
        spinner.color = title.textColor
        bar.progressTintColor = .init(red: 0.86, green: 0.72, blue: 0.42, alpha: 1)
        bar.trackTintColor = .init(white: 1, alpha: 0.15)
        bar.accessibilityIdentifier = "loadingProgress"
        retry.setTitle("重新加载", for: .normal)
        retry.addTarget(self, action: #selector(retryLoading), for: .touchUpInside)
        let stack = UIStackView(arrangedSubviews: [title, spinner, status, bar, retry])
        stack.axis = .vertical; stack.spacing = 18
        stack.translatesAutoresizingMaskIntoConstraints = false
        addSubview(stack)
        NSLayoutConstraint.activate([
            stack.centerXAnchor.constraint(equalTo: centerXAnchor), stack.centerYAnchor.constraint(equalTo: centerYAnchor),
            stack.widthAnchor.constraint(equalToConstant: 280)
        ])
        update(0, text: "准备进入林地")
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    func update(_ progress: Float, text: String) {
        bar.progress = max(bar.progress, min(1, progress))
        status.text = "\(text) · \(Int(bar.progress * 100))%"
        retry.isHidden = true; spinner.startAnimating()
    }

    func failed(_ error: Error) {
        spinner.stopAnimating(); retry.isHidden = false
        status.text = "加载失败，请重试"
        accessibilityHint = error.localizedDescription
    }

    @objc private func retryLoading() {
        bar.progress = 0; update(0, text: "准备进入林地"); onRetry?()
    }
}
