# Đề bài: Chatbot NextFarm — Bản tóm tắt kỹ thuật để bắt đầu code

> File này tổng hợp lại nội dung tài liệu `DebaiChatbotNextFarm.pdf` trong Project, ở dạng Markdown để dùng làm ngữ cảnh (context) khi bắt đầu một phiên Claude Code cho dự án. Đặt file này vào thư mục gốc của repo (ví dụ đặt tên `SPEC.md` hoặc `CLAUDE.md`) rồi mở tab **Code** trong app Claude, trỏ tới thư mục đó và bắt đầu phiên.

## 1. Bối cảnh sản phẩm

NextFarm là nền tảng nông nghiệp thông minh gồm ba lớp:

- **Lớp thiết bị (IoT):** bộ điều khiển tưới trên nền ESP32 (bản 3 cổng và 4 cổng). Đóng/mở van tưới, bơm, van châm phân theo lịch hoặc lệnh tay; đọc cảm biến qua RS485/Modbus (độ ẩm đất, nhiệt độ, EC, pH, lưu lượng...); kết nối server qua MQTT (Ethernet/WiFi); có OTA cập nhật firmware.
- **Lớp nền tảng (backend):** hai dịch vụ .NET — IAM Service (người dùng, khách hàng, phân quyền) và IoT Service (nhận dữ liệu MQTT, lưu trạng thái thiết bị, lịch tưới, lịch sử tưới, nhật ký lệnh, cảnh báo; đẩy realtime qua SignalR).
- **Lớp ứng dụng:** Web (Next.js, app.nextfarm.vn) và app di động (Flutter, iOS/Android).

Người dùng cuối: chủ vườn/nông dân và kỹ thuật viên tại Việt Nam, phần lớn không rành công nghệ, dùng điện thoại là chính, giao tiếp bằng tiếng Việt đời thường pha thuật ngữ nông nghiệp địa phương.

## 2. Hiện trạng chatbot

| Hạng mục | Hiện tại |
|---|---|
| Trạng thái | Đã chạy thật với khách hàng |
| Kênh | Zalo OA + khung chat trong app NextFarm |
| Lõi xử lý | Gọi API mô hình ngôn ngữ lớn (LLM) |
| RAG / kho tri thức | Chưa có |
| Kết nối dữ liệu vườn thật | Chưa có — bot chỉ trả lời dựa trên kiến thức sẵn có của mô hình |

## 3. Năng lực mong muốn

1. **Hỏi đáp dữ liệu vườn** — ví dụ: "Độ ẩm đất khu A giờ bao nhiêu?", "Hôm qua tưới mấy lần?", "Van số 3 có đang chạy không?"
2. **Điều khiển thiết bị bằng hội thoại** — ví dụ: "Bật van 3 trong 10 phút". Bắt buộc có bước xác nhận + kiểm tra phân quyền vì đây là hành động vật lý.
3. **Cảnh báo chủ động + giải thích sự cố** — chủ động báo khi mất kết nối/cảm biến bất thường/lịch tưới lỗi, kèm giải thích nguyên nhân và cách xử lý.
4. **Tư vấn nông học & hỗ trợ khách hàng** — câu hỏi kỹ thuật canh tác, hướng dẫn dùng app, tra cứu tài liệu.

## 4. Hai bài toán chính cần giải

### Bài toán A — Bot trả lời sai / bịa đặt
Chatbot bịa số liệu vườn, bịa tính năng không tồn tại, khuyến nghị canh tác không phù hợp, hoặc hiểu sai tiếng Việt của nông dân. Cần:
- Kiến trúc chống bịa (RAG trên kho tri thức nội bộ / fine-tune / bắt buộc trích dẫn nguồn / cơ chế "không biết thì nói không biết")
- Cách xây và duy trì kho tri thức nông học tiếng Việt
- Xử lý tiếng Việt nông nghiệp: từ địa phương, viết tắt, không dấu, lỗi chính tả
- Bộ đo chất lượng: đo độ chính xác, tập kiểm thử, ngưỡng đạt

### Bài toán B — Không truy được dữ liệu IoT thời gian thực
Bot không biết gì về vườn của người hỏi. Dữ liệu NextFarm có sẵn, có thể mở API:

| Nhóm dữ liệu | Nội dung | Nhịp cập nhật |
|---|---|---|
| Số đo cảm biến | Độ ẩm đất, nhiệt độ, EC, pH, lưu lượng theo thiết bị/khu | ~10 phút |
| Trạng thái thiết bị | Online/offline, trạng thái từng cổng ra | ~5 giây |
| Lịch tưới | Cấu hình ca tưới: khu, van, thời lượng | Theo cấu hình |
| Lịch sử tưới | Ca đã chạy: bắt đầu, kết thúc, thời lượng, lượng nước | Theo sự kiện |
| Nhật ký lệnh điều khiển | Ai ra lệnh gì, lúc nào, kết quả | Theo sự kiện |
| Cảnh báo | Mất kết nối, vượt ngưỡng cảm biến | Theo sự kiện |
| Hồ sơ khách hàng/vườn | Cây trồng, diện tích, phân khu | Tĩnh |

Cần đề xuất: mô hình tích hợp (function calling/tool use, MCP server, hay đồng bộ dữ liệu), cách ánh xạ tài khoản Zalo OA ↔ tài khoản NextFarm + phân quyền dữ liệu, cách diễn giải số liệu thô thành câu trả lời hữu ích, cách xử lý dữ liệu thiếu/trễ.

## 5. Ràng buộc bắt buộc

- **An toàn điều khiển:** mọi lệnh tác động thiết bị phải qua xác nhận rõ ràng + kiểm tra phân quyền; không được đi vòng qua các quy tắc an toàn ở tầng firmware (ví dụ: tắt bơm thì dừng cả ca tưới để chống thuỷ kích).
- **Bảo mật dữ liệu:** làm rõ dữ liệu nào gửi ra ngoài, gửi cho nhà cung cấp mô hình nào, lưu trữ ở đâu, bao lâu.
- **Ngôn ngữ:** tiếng Việt là chính, câu trả lời ngắn, dễ hiểu với người không rành công nghệ.
- **Chi phí & hạ tầng:** cần ước lượng chi phí theo lượng hội thoại; so sánh self-host vs API bên thứ ba.
- **Độ trễ:** hỏi trạng thái vườn cần trả lời trong vài giây.

## 6. Tiêu chí nghiệm thu (PoC)

- Bot trả lời đúng ≥ 95% câu hỏi tra cứu số liệu vườn, đối chiếu dữ liệu gốc trong hệ thống
- Khi không có dữ liệu, bot nói rõ "không có dữ liệu" thay vì đoán — tỷ lệ bịa gần bằng 0 trên tập kiểm thử
- Không có trường hợp bot truy cập dữ liệu của vườn không thuộc quyền người hỏi
- Thời gian phản hồi trung bình dưới ngưỡng [cần điền] giây

## 7. Gợi ý điểm bắt đầu khi code

- Thiết kế MCP server / tầng tool-calling để chatbot gọi API IoT Service (đọc cảm biến, trạng thái thiết bị, lịch tưới, lịch sử) và IAM Service (xác thực, phân quyền theo vườn).
- Xây pipeline RAG cho kho tri thức nông học tiếng Việt (nguồn dữ liệu, chunking, embedding, retrieval, trích dẫn nguồn).
- Thiết kế luồng xác nhận (confirmation flow) bắt buộc cho mọi lệnh điều khiển thiết bị, có kiểm tra phân quyền trước khi gọi API điều khiển.
- Viết bộ test/eval đo độ chính xác trả lời số liệu vườn và tỷ lệ "bịa" khi thiếu dữ liệu.
