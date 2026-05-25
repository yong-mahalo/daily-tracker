import Foundation
import Combine

class DataFetcher: ObservableObject {
    @Published var widgetData: WidgetData? = nil
    @Published var isOffline: Bool = false
    @Published var logStatus: String = ""   // feedback after submitting a log
    @Published var shouldHide: Bool = false

    private var timer: Timer?
    private let baseURL = "http://localhost:8090"

    func start() {
        fetch()
        timer = Timer.scheduledTimer(withTimeInterval: 60, repeats: true) { [weak self] _ in
            self?.fetch()
        }
    }

    func fetch() {
        let url = URL(string: "\(baseURL)/api/widget")!
        var req = URLRequest(url: url, timeoutInterval: 5)
        req.cachePolicy = .reloadIgnoringLocalCacheData

        URLSession.shared.dataTask(with: req) { [weak self] data, _, _ in
            DispatchQueue.main.async {
                guard let self else { return }
                if let data, let decoded = try? JSONDecoder().decode(WidgetData.self, from: data) {
                    self.widgetData = decoded
                    self.isOffline = false
                } else {
                    self.isOffline = true
                }
            }
        }.resume()
    }

    func submitLog(_ text: String, completion: @escaping (Bool) -> Void) {
        guard !text.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        let url = URL(string: "\(baseURL)/api/log/json")!
        var req = URLRequest(url: url, timeoutInterval: 10)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try? JSONEncoder().encode(["raw_text": text])

        URLSession.shared.dataTask(with: req) { [weak self] _, response, _ in
            DispatchQueue.main.async {
                let ok = (response as? HTTPURLResponse)?.statusCode == 200
                self?.logStatus = ok ? "✓ Logged" : "✗ Error"
                completion(ok)
                if ok {
                    // refresh data after a short delay
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) {
                        self?.fetch()
                        self?.logStatus = ""
                    }
                }
            }
        }.resume()
    }

    deinit { timer?.invalidate() }
}
