import UIKit
import WebKit

class WebViewController: UIViewController {
    
    // MARK: - Properties
    private var webView: WKWebView!
    private var progressView: UIProgressView!
    private var refreshControl: UIRefreshControl!
    private var observation: NSKeyValueObservation?
    
    // Change this URL to your deployed app URL
    private let appURL = URL(string: "https://your-deployed-app-url.replit.app")!
    
    // MARK: - Lifecycle Methods
    override func viewDidLoad() {
        super.viewDidLoad()
        setupNavigationBar()
        configureWebView()
        setupProgressView()
        setupRefreshControl()
        loadWebContent()
    }
    
    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        startObservingProgress()
    }
    
    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        observation?.invalidate()
    }
    
    // MARK: - Setup Methods
    private func setupNavigationBar() {
        title = "Calm Journey"
        
        // Add refresh button
        let refreshButton = UIBarButtonItem(barButtonSystemItem: .refresh, target: self, action: #selector(refreshTapped))
        
        // Add home button
        let homeButton = UIBarButtonItem(image: UIImage(systemName: "house"), style: .plain, target: self, action: #selector(homeTapped))
        
        navigationItem.rightBarButtonItems = [refreshButton, homeButton]
    }
    
    private func configureWebView() {
        // Configure WebView preferences
        let preferences = WKWebpagePreferences()
        preferences.allowsContentJavaScript = true
        
        let configuration = WKWebViewConfiguration()
        configuration.defaultWebpagePreferences = preferences
        
        // Enable features needed for PWA support
        configuration.allowsInlineMediaPlayback = true
        configuration.mediaTypesRequiringUserActionForPlayback = []
        
        // Create the web view
        webView = WKWebView(frame: view.bounds, configuration: configuration)
        webView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        webView.navigationDelegate = self
        webView.uiDelegate = self
        
        view.addSubview(webView)
    }
    
    private func setupProgressView() {
        progressView = UIProgressView(progressViewStyle: .default)
        progressView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(progressView)
        
        NSLayoutConstraint.activate([
            progressView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            progressView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            progressView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            progressView.heightAnchor.constraint(equalToConstant: 2)
        ])
    }
    
    private func setupRefreshControl() {
        refreshControl = UIRefreshControl()
        refreshControl.addTarget(self, action: #selector(refreshWebView), for: .valueChanged)
        webView.scrollView.addSubview(refreshControl)
    }
    
    private func startObservingProgress() {
        observation = webView.observe(\.estimatedProgress, options: [.new]) { [weak self] webView, change in
            guard let self = self else { return }
            
            self.progressView.progress = Float(webView.estimatedProgress)
            
            // Show/hide progress view based on load state
            if webView.estimatedProgress >= 1.0 {
                UIView.animate(withDuration: 0.3, delay: 0.3, options: .curveEaseOut, animations: {
                    self.progressView.alpha = 0
                }, completion: { finished in
                    self.progressView.progress = 0
                })
            } else {
                UIView.animate(withDuration: 0.3, delay: 0, options: .curveEaseIn, animations: {
                    self.progressView.alpha = 1
                }, completion: nil)
            }
        }
    }
    
    private func loadWebContent() {
        let request = URLRequest(url: appURL, cachePolicy: .returnCacheDataElseLoad)
        webView.load(request)
    }
    
    // MARK: - Action Methods
    @objc private func refreshTapped() {
        refreshWebView()
    }
    
    @objc private func homeTapped() {
        let request = URLRequest(url: appURL, cachePolicy: .returnCacheDataElseLoad)
        webView.load(request)
    }
    
    @objc private func refreshWebView() {
        webView.reload()
        refreshControl.endRefreshing()
    }
}

// MARK: - WKNavigationDelegate
extension WebViewController: WKNavigationDelegate {
    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = navigationAction.request.url else {
            decisionHandler(.cancel)
            return
        }
        
        // Handle external links
        if url.host != appURL.host && (url.scheme == "http" || url.scheme == "https") {
            UIApplication.shared.open(url)
            decisionHandler(.cancel)
            return
        }
        
        decisionHandler(.allow)
    }
    
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        // Add any JavaScript to be executed after page load
        // For example, disabling pinch-to-zoom if it interferes with your UI
        /*
        webView.evaluateJavaScript("""
            document.documentElement.style.webkitTouchCallout = 'none';
            document.documentElement.style.webkitUserSelect = 'none';
            """, completionHandler: nil)
        */
    }
    
    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        refreshControl.endRefreshing()
        handleNavigationError(error)
    }
    
    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        refreshControl.endRefreshing()
        handleNavigationError(error)
    }
    
    private func handleNavigationError(_ error: Error) {
        // Handle errors like no network connection
        if let error = error as NSError?, error.code == NSURLErrorNotConnectedToInternet {
            let alertController = UIAlertController(
                title: "Connection Error",
                message: "Could not connect to Calm Journey. Please check your internet connection and try again.",
                preferredStyle: .alert
            )
            
            alertController.addAction(UIAlertAction(title: "Retry", style: .default) { [weak self] _ in
                self?.loadWebContent()
            })
            
            alertController.addAction(UIAlertAction(title: "Cancel", style: .cancel))
            
            present(alertController, animated: true)
        }
    }
}

// MARK: - WKUIDelegate
extension WebViewController: WKUIDelegate {
    // Handle JavaScript alerts
    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let alertController = UIAlertController(title: "Alert", message: message, preferredStyle: .alert)
        alertController.addAction(UIAlertAction(title: "OK", style: .default, handler: { _ in
            completionHandler()
        }))
        present(alertController, animated: true)
    }
    
    // Handle JavaScript confirm dialogs
    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let alertController = UIAlertController(title: "Confirm", message: message, preferredStyle: .alert)
        
        alertController.addAction(UIAlertAction(title: "OK", style: .default, handler: { _ in
            completionHandler(true)
        }))
        
        alertController.addAction(UIAlertAction(title: "Cancel", style: .cancel, handler: { _ in
            completionHandler(false)
        }))
        
        present(alertController, animated: true)
    }
    
    // Handle JavaScript text input dialogs
    func webView(_ webView: WKWebView, runJavaScriptTextInputPanelWithPrompt prompt: String, defaultText: String?, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (String?) -> Void) {
        let alertController = UIAlertController(title: "Prompt", message: prompt, preferredStyle: .alert)
        
        alertController.addTextField { textField in
            textField.text = defaultText
        }
        
        alertController.addAction(UIAlertAction(title: "OK", style: .default, handler: { _ in
            if let text = alertController.textFields?.first?.text {
                completionHandler(text)
            } else {
                completionHandler(defaultText)
            }
        }))
        
        alertController.addAction(UIAlertAction(title: "Cancel", style: .cancel, handler: { _ in
            completionHandler(nil)
        }))
        
        present(alertController, animated: true)
    }
}