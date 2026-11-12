# Rà soát UI "Đường An" (Luna, 2026-11-12)

Phạm vi: `frontend/src/main.tsx`, `frontend/src/style.css` sau đợt sửa UI (TracePipeline, SourceList, tab Kiến trúc, a11y). Chỉ đề xuất trong frontend, không đổi API.

## 0. Cách rà và giới hạn

- **Không xem được bằng trình duyệt.** Thử `tabs_context_mcp` (claude-in-chrome) lần 1: "Browser extension is not connected". Theo yêu cầu, bỏ qua và rà bằng đọc code + gọi API thật (`/api/chat`, `/api/learning`, `/api/health` ở 127.0.0.1:8001) + đối chiếu ảnh bảng `IMG_7908.jpeg` và `docs/HUONG_DAN_KIEN_TRUC.md` mục 2-3.
- Chưa kiểm bằng mắt, cần Kit/Hawk xác nhận khi chạy thật: bố cục 390px (nav 5 mục cuộn ngang, chat cao cố định), bàn phím ảo che ô nhập, độ rộng thực của pipeline. Các mục này đánh dấu "(chưa kiểm)".
- Tỉ lệ tương phản đã tính bằng công thức WCAG 2.2 cho các cặp màu đọc từ CSS. Cặp ước lượng ghi "~".
- Dữ liệu API thật dùng làm căn cứ:
  - Chat thường: `trace = ["Coordinator","Rule Agent","Rule Agent (Approved)","Knowledge Agent (Retrieved 3 sources)","Knowledge Graph Agent (3 facts, +0 linked docs)","Response Agent (Cited Generation)"]`. `sources` gồm 3 nguồn web đã tóm tắt + 1 nguồn `review_status="curated_graph"`. Một nguồn không liên quan câu hỏi về bàn chân ("Sức khỏe tinh thần...").
  - Câu cấp cứu: `trace = [..., "Rule Agent (Blocked: EMERGENCY)", "Response Agent (Safety Directive)"]`, `sources = []`, `answer` bắt đầu bằng emoji và viết HOA toàn bộ.
  - `/api/learning`: `{"topic","action","trace":["Coordinator","Learning Agent (DQN Policy)"],"policy_overridden","disclaimer":"Mô phỏng giáo dục mô phỏng; ..."}`. Khi bỏ chọn hết: `status:"completed"` + `message`.

## 1. Tóm tắt

| Mức | Số vấn đề | Ý chính |
| --- | --- | --- |
| 4 (chặn demo) | 0 | |
| 3 (nghiêm trọng) | 6 | Trace hiện chuỗi tiếng Anh/trùng bước; bong bóng trả lời trống không báo chờ; lỗi mạng hiện "Failed to fetch"; điểm "Lớp 0/1" dễ hiểu sai y tế; tab Kiến trúc đặt RL+Rule sai chỗ so với bảng; câu cấp cứu hiển thị như văn bản thường |
| 2 (đáng kể) | 10 | Không có nút Dừng/Thử lại; auto-scroll mỗi token; trace luôn mở; live region aside quá rộng; tương phản chữ nhỏ; thiếu nhắc y tế mỗi câu trả lời; claim "nguồn chính thức"; form 15 chỉ số thiếu hướng dẫn; trạng thái dịch vụ mơ hồ; thiếu skip link |
| 1 (nhẹ) | 8 | Thuật ngữ lẫn lộn, glyph ✳ đọc thành "asterisk", heading nhảy cấp, đếm ký tự, mất dữ liệu khi đổi tab, v.v. |

Điểm tốt cần giữ: `role="log"` + `aria-busy`, `:focus-visible` rõ, `.sr-only` cho "mở trong tab mới", badge nguồn có chữ (không chỉ màu), `prefers-reduced-motion` trong CSS, chặn Enter khi gõ IME bằng `isComposing`, khôi phục câu hỏi vào ô nhập khi lỗi, nút vùng chạm 44px ở ≤800px.

## 2. Đánh giá theo 10 heuristic Nielsen (0 = không vấn đề, 4 = thảm họa)

| # | Heuristic | Mức | Ghi chú chính |
| --- | --- | --- | --- |
| H1 | Hiển thị trạng thái hệ thống | 3 | Bong bóng trả lời trống trong lúc chờ (V-02); trạng thái dịch vụ không nói dịch vụ nào lỗi (V-12); không có chỉ báo "đang viết" khi stream |
| H2 | Khớp hệ thống với thế giới thực | 3 | "Lớp 0/Lớp 1", "Score / 1", "Approved", "Cited Generation", "+0 linked docs" (V-01, V-05) |
| H3 | Người dùng kiểm soát và tự do | 2 | Không dừng được câu trả lời đang stream, không "Thử lại"; đổi tab bộ dữ liệu xóa số đã nhập không báo (V-09, V-18) |
| H4 | Nhất quán và chuẩn | 2 | Lẫn "agent/tác tử/Agent", "Tổng quan" vs "Trang chủ"; hai nhãn NHANES gần giống nhau (V-17) |
| H5 | Ngăn lỗi | 2 | Không giới hạn trước khi nhập quá miền (có min/max nhưng không gợi ý khoảng); không đếm ký tự 1500 |
| H6 | Nhận biết hơn ghi nhớ | 2 | Form 15 chỉ số không nói lấy từ đâu; RL không giải thích kết quả (V-13, V-14) |
| H7 | Linh hoạt và hiệu quả | 1 | Có câu hỏi gợi ý, Enter gửi; thiếu skip link (V-16) |
| H8 | Thiết kế tối giản và thẩm mỹ | 2 | Trace mở hết ở mọi câu trả lời làm chat dài (V-07); tiêu đề lặp "Luồng xử lý..." và "Quá trình xử lý..." |
| H9 | Giúp nhận biết, chẩn đoán, khắc phục lỗi | 3 | Lỗi mạng/JSON hiện nguyên văn kỹ thuật (V-03); lỗi không có hướng khắc phục |
| H10 | Trợ giúp và tài liệu | 2 | Tab Kiến trúc chưa giải thích "một câu hỏi đi qua đâu" (V-05); nhắc y tế chỉ ở chân trang chat |

## 3. Danh sách vấn đề

Cột "WCAG" là tiêu chí WCAG 2.2 liên quan nếu có.

| ID | Mức | Vị trí | Vấn đề | WCAG |
| --- | --- | --- | --- | --- |
| V-01 | 3 | `TracePipeline` | Trace hiện nguyên chuỗi backend: tiếng Anh ("Approved", "Retrieved 3 sources", "Cited Generation", "Safety Directive", "Blocked: EMERGENCY"), thuật ngữ ("+0 linked docs"), và bước trùng ("Rule Agent" rồi "Rule Agent (Approved)") nên "6 bước" thực chất chỉ 5 tác tử. Giảng viên đọc không hiểu. | 3.1.5 gợi ý |
| V-02 | 3 | Chat, bong bóng assistant | `sendChat` thêm bong bóng assistant rỗng ngay khi response ok, trong khi điều kiện hiện "đang kiểm tra" là `last.role !== 'assistant'`. Hệ quả: lúc chờ token đầu (Ollama có thể vài giây) chỉ thấy bong bóng trống, không chữ, không báo. | 4.1.3 |
| V-03 | 3 | `postApi`, `sendChat` catch | `e.message` hiện thẳng: "Failed to fetch" (TypeError), "Unexpected token < in JSON" khi proxy trả HTML, `detail` của API có thể là tiếng Anh. Không có hướng khắc phục. | 3.3.1, 3.3.3 |
| V-04 | 3 | Kết quả dự đoán | "0.874 / 1" + "Lớp dự đoán tại ngưỡng 0.5: Lớp 1" dễ bị đọc là xác suất mắc bệnh / "bạn có bệnh". Thuật ngữ "Lớp 0/1" không có nghĩa với người dùng. Dùng dấu chấm thay vì dấu phẩy thập phân vi-VN. Cảnh báo "không phải chẩn đoán" nằm cuối, chữ nhỏ. | 3.1.5 |
| V-05 | 3 | Tab Kiến trúc | Không khớp bảng: (a) "Reinforcement Learning + Rule" đặt ở cột "Nguồn dữ liệu và tri thức", trong khi bảng vẽ RL và Rule là hai khối đi vào Agent trung tâm, và tài liệu mục 2.1 nói Rule Agent chặn trước RAG; (b) mũi tên cột-sang-cột ngụ ý mọi khối nối mọi khối, mất luồng DB → Deep Learning → Dự đoán/Phân loại, mất "web, sách → tạo KB", mất cổng Rule trước RAG; (c) Người dùng ở cuối, không có vòng tư vấn/trợ giúp; (d) không có chú giải màu liên hệ với trace trong chat. Đã có đủ Knowledge Graph Agent, Prediction Agent, Learning Agent (RL), Rule Agent; thiếu nguồn "web, sách" tạo KB. | |
| V-06 | 3 | Chat, trả lời bị chặn cấp cứu | Câu cảnh báo khẩn (viết HOA, emoji 🚨) hiển thị cùng kiểu bong bóng thường, không có `Blocked` rõ ràng trong trace, nguồn rỗng không giải thích. Người dùng cần thấy ngay đây là cảnh báo an toàn và số 115. | 1.4.1, 4.1.3 |
| V-07 | 2 | Chat, `details open` | Mọi câu trả lời đều mở sẵn trace 5-6 thẻ; sau 3 lượt chat dài gấp đôi. Heading trong `details` lặp lại summary. Trên 390px mỗi pipeline cao ~400px (chưa kiểm). | |
| V-08 | 2 | Chat, cuộn | `scrollIntoView({behavior:'smooth'})` chạy mỗi lần `conversation` đổi (mỗi token): giật, cướp vị trí khi người dùng cuộn lên đọc; tùy chọn `smooth` tường minh không bị CSS `scroll-behavior:auto` ghi đè nên vi phạm giảm chuyển động. | 2.3.3 gợi ý |
| V-09 | 2 | Chat, điều khiển | Không có nút Dừng khi đang stream; khi lỗi giữa chừng thông báo lỗi nối vào cuối bong bóng nhưng không có "Thử lại". | |
| V-10 | 2 | Chat, live region | `role="log"` + `aria-live="polite"` đúng hướng, nhưng bong bóng "đang kiểm tra" có `role="status"` riêng và header cũng có `role="status"`; chưa có thông báo hoàn tất ("Đã trả lời xong, N nguồn"). Trace mở sẵn khiến trình đọc màn hình đọc hết danh sách. | 4.1.3 |
| V-11 | 2 | Tương phản | `.chat-trace` `#829589` trên `#f2f7f1` = 2.93:1 (11px); nav `#74857c` 13px trên nền sáng ~3.7:1; `.brand small` `#80928a` 8px ~3.2:1. Cần ≥ 4.5:1. Các cặp còn lại đạt: `#5f6f66`/`#f7f7f4` 4.95, `#596c61`/`#f7f7f4` 5.23, trắng/`#386a50` 6.28, `#3f5a4c`/`#f1f6f1` 6.91. | 1.4.3 |
| V-12 | 2 | Header trạng thái | "Một số dịch vụ chưa sẵn sàng" không nói Neo4j hay Ollama, không nói ảnh hưởng gì; chat vẫn cho gửi rồi lỗi. | 3.3.1 |
| V-13 | 2 | Form 15 chỉ số | 13 ô số liền nhau không nhóm; "ALT", "Creatinine", "HbA1c" không giải thích; không ghi "lấy từ phiếu xét nghiệm"; nhãn "Giới tính theo mã khảo sát NHANES" khó hiểu; placeholder select dạng "-- Chọn câu trả lời --"; chỉ dùng kiểm tra HTML gốc, không có tóm tắt lỗi. | 3.3.2 |
| V-14 | 2 | Tab RL, kết quả | Chỉ hiện tên chủ đề + trace. Không nói đây là đề xuất của DQN, không nói khi `policy_overridden=true` thì luật đã chỉnh; disclaimer backend "Mô phỏng giáo dục mô phỏng" lặp từ. Trạng thái bỏ chọn hết trả `completed` + message: hợp lý, giữ. | |
| V-15 | 2 | Trang chủ + chat | Hero "KIẾN THỨC Y TẾ DỰA TRÊN DỮ LIỆU & NGUỒN CHÍNH THỨC" quá mức khi hệ thống có nguồn web chưa kiểm duyệt; chat không có một dòng nhắc y tế dưới mỗi câu trả lời (backend có `disclaimer` nhưng stream `done` không dùng). Mỗi câu y tế cần nhắc đúng mức, ngắn. | |
| V-16 | 2 | Toàn trang | Không có skip link; `<main>` không có id; kết quả (aside) nằm dưới form trên mobile, sau khi gửi không chuyển focus/cuộn tới. `aria-live="polite"` trên cả `<aside>` sẽ đọc toàn bộ nội dung kết quả. | 2.4.1, 4.1.3 |
| V-17 | 1 | Nhãn | Hai tab "NHANES 15 chỉ số" và "Chỉ số xét nghiệm (NHANES thử nghiệm)" khó phân biệt; trộn "agent/tác tử/Agent"; "Hỏi đáp đa agent". | 3.2.4 |
| V-18 | 1 | Form | Đổi bộ dữ liệu xóa `values` và kết quả không báo; nhóm tab dùng `aria-pressed` (chấp nhận được) nhưng là chọn một trong bốn, nên dùng radio/tablist. | 3.2.2 |
| V-19 | 1 | Glyph ✳ | Không `aria-hidden` ở logo, brand, avatar, emptyicon: trình đọc đọc "dấu hoa thị". | 1.1.1 |
| V-20 | 1 | Nguồn | Tiêu đề nguồn đồ thị lặp tiền tố "Đồ thị tri thức Neo4j:" đã có trong badge; hai nguồn cùng URL; `[n]` trong câu trả lời không nhấp được; có nguồn lệch chủ đề (vấn đề truy xuất phía backend, báo Atlas). | |
| V-21 | 1 | Heading | Tab Kiến trúc đi `h1 -> h3` (thiếu h2). Tab Chat: `h2` trong welcome sau `h1` ổn. | 1.3.1 |
| V-22 | 1 | Ô nhập chat | `maxLength=1500` cắt im lặng, không đếm; chat cao cố định 430-470px (chưa kiểm với bàn phím ảo 390px). | |
| V-23 | 1 | Trang chủ | Đoạn giới thiệu liệt kê agent bằng tiếng Anh, thiếu Knowledge Graph Agent; không có thẻ dẫn tới tab Kiến trúc. | |
| V-24 | 1 | Header nav | Hover/active chỉ gạch chân màu nhạt; ở ≤800px nav cuộn ngang không có dấu hiệu còn mục phía sau (chưa kiểm). | 1.4.11 |

## 4. Ma trận trạng thái (hiện tại và thiếu)

Ký hiệu: OK = đã có và đạt; THIẾU = chưa có; SỬA = có nhưng lỗi, xem V-xx.

| Màn hình | Loading | Streaming | Empty | Error | Success |
| --- | --- | --- | --- | --- | --- |
| Chat | SỬA: bong bóng trống (V-02) | THIẾU: chỉ báo "đang viết", nút Dừng (V-09) | OK: welcome + 4 câu gợi ý | SỬA: chuỗi kỹ thuật, không Thử lại (V-03, V-09) | SỬA: nguồn + trace OK, thiếu nhắc y tế (V-15), thông báo hoàn tất (V-10) |
| Chat, bị chặn an toàn | như trên | như trên | | | THIẾU: kiểu cảnh báo riêng (V-06) |
| Form dự đoán | OK: nút "Đang phân tích dữ liệu…" (disabled) | không áp dụng | SỬA: aside "Sẵn sàng hỗ trợ bạn" chưa nói rõ bước tiếp theo | SỬA: lỗi chỉ hiện dưới form, không có tóm tắt, thông điệp kỹ thuật (V-03, V-13) | SỬA: Lớp 0/1 (V-04) |
| Tab RL | OK: "Đang suy luận chính sách…" | không áp dụng | OK: mặc định chọn hết 4 chủ đề | như form | SỬA: thiếu giải thích, `policy_overridden` (V-14); bỏ chọn hết đã trả message hoàn thành |
| Tab Kiến trúc | tĩnh | tĩnh | tĩnh | không áp dụng (không gọi API) | SỬA: bố cục (V-05) |
| Toàn trang | `health` chưa tải: hiện "Không kết nối được API" nhấp nháy sai (nên "Đang kiểm tra…") | | | THIẾU: chi tiết dịch vụ (V-12) | OK |

## 5. Tab Kiến trúc đối chiếu bảng `IMG_7908.jpeg` và tài liệu

Hình trên bảng (đọc từ ảnh): DB có sẵn → Deep Learning → Dự toán / Phân loại, đi xuống một "bộ não" trung tâm có chữ "tư vấn + trợ giúp"; Neo4j KB + RAG + Agent bên trái, "web, book" tạo KB; hai khối Reinforcement Learning và Rule đi vào Agent trung tâm.

| Thành phần theo bảng/tài liệu | Có trên tab? | Nhận xét |
| --- | --- | --- |
| DB có sẵn (UCI/BRFSS/NHANES) | Có, là một hộp | Thiếu mũi tên "Deep Learning → Dự đoán/Phân loại → Prediction Agent" |
| Deep Learning → Dự đoán / Phân loại | Chỉ trong mô tả Prediction Agent | Nên là bước rõ ràng |
| Neo4j KB + RAG | Có | Tốt |
| web, sách → tạo KB | Chỉ trong mô tả "xây từ web và sách" | Thiếu nút nguồn |
| Knowledge Graph Agent (tài liệu mục 2.1, 3) | Có | OK, nên ghi "Cypher" |
| Prediction Agent | Có | OK |
| Learning Agent RL + Rule | Rule Agent và Learning Agent có; hộp "RL + Rule" ở cột 1 | Sai vai trò: không phải nguồn dữ liệu (V-05a) |
| Rule chặn trước RAG | Không | Mất ý quan trọng nhất của tài liệu 2.2 |
| Tư vấn / trợ giúp | Hộp "Người dùng" | Nên là đầu ra "Tư vấn / trợ giúp" |
| Coordinator, Response Agent, Conversation Agent | Có | OK |

Bố cục đề xuất (CSS grid, không cần thư viện): 3 lớp ngang, mỗi lớp là một `<section>` có `<h2>`:
1. **Dữ liệu và tri thức** (DB UCI/BRFSS/NHANES; web, sách → Neo4j KB gồm Document+embedding và đồ thị thực thể).
2. **Các tác tử** (Prediction, Knowledge RAG, Knowledge Graph, Rule, Learning RL, Conversation), mỗi hộp có ô nhỏ "đọc từ: ...".
3. **Điều phối và phản hồi** (Coordinator, Response Agent, Tư vấn / trợ giúp).
Dưới cùng là danh sách có thứ tự "Một câu hỏi đi qua đâu" (5 bước theo `HUONG_DAN_KIEN_TRUC.md` mục 3) và chú giải màu trùng màu trace.

## 6. Bảng handoff cho Kit

Quy ước: mọi đường dẫn trong `frontend/src/`. Không đổi API; xử lý chuỗi bằng hàm hiển thị ở frontend. Màu giữ nguyên bảng hiện có trừ khi ghi khác.

| ID | Screen / component | Vấn đề | Thay đổi cụ thể | Copy chính xác | State | Tiêu chí chấp nhận |
| --- | --- | --- | --- | --- | --- | --- |
| K-01 | `TracePipeline` (V-01) | Chuỗi Anh, bước trùng | Thêm hàm `formatTrace(trace: string[])` trả `{name, detail, status}[]`. Bỏ bước bare khi bước kế tiếp có cùng tên + `(…)` (vd "Rule Agent" rồi "Rule Agent (Approved)"). Bỏ bước "Coordinator" khỏi đếm hoặc gộp thành tiêu đề. Dịch `detail` theo bảng bên dưới; chi tiết không khớp bảng thì hiện nguyên văn trong `<small>` không dịch. Số bước trong tiêu đề = số bước hiển thị | Bảng dịch: `Approved` -> "Đã duyệt, không có dấu hiệu nguy hiểm"; `Retrieved N sources` -> "Tìm thấy N tài liệu"; `N facts, +M linked docs` -> "N sự kiện từ đồ thị" (bỏ phần `+M` nếu M=0, nếu M>0 thêm ", kèm M tài liệu gốc"); `Cited Generation` -> "Viết câu trả lời có trích dẫn nguồn"; `Safety Directive` -> "Gửi hướng dẫn an toàn"; `Blocked: EMERGENCY` -> "Dừng: phát hiện dấu hiệu cấp cứu"; `Blocked: …` khác -> "Dừng: yêu cầu bị chặn vì lý do an toàn"; `DQN Policy` -> "Chính sách DQN chọn chủ đề"; `All modules completed` -> "Đã học hết các chủ đề". Tên tác tử giữ nguyên (Rule Agent, Knowledge Graph Agent...) | Có chuỗi, Có `Blocked` | Với trace thật ở mục 0: hiển thị 5 thẻ, không có chữ tiếng Anh nào ngoài tên riêng tác tử, không thẻ trùng. Với trace cấp cứu: thẻ Rule Agent có nhãn "Dừng: ..." và không có thẻ Knowledge |
| K-02 | `TracePipeline` + `.chat-trace` (V-07, V-11) | Mở hết, tiêu đề lặp, tương phản | Chỉ `open` cho câu trả lời assistant cuối cùng; các câu cũ đóng. Đổi tiêu đề `.trace-title` thành ẩn khi nằm trong `details` (dùng prop `hideTitle`). Đổi `.chat-trace` màu sang `#3f5a4c`, font 12px | Summary: "Các bước xử lý (N)". Tiêu đề ngoài chat (aside): "Luồng xử lý của hệ đa tác tử (N bước)" | Chat nhiều lượt | Sau 3 lượt chỉ một trace đang mở; mọi chữ trong `.chat-trace` tương phản ≥ 4.5:1; summary vẫn mở được bằng Enter/Space |
| K-03 | Chat, bong bóng trống (V-02, V-10) | Chờ token đầu không có chỉ báo | Không tạo bong bóng assistant rỗng. Điều kiện hiện chỉ báo: `busy && (last.role !== 'assistant' \|\| last.content === '')`; hiển thị chỉ báo bên trong bong bóng đó. Giữ một `role="status"` duy nhất trong vùng chat, text cập nhật theo giai đoạn: chờ, đang viết, xong | Chờ: "Đang kiểm tra an toàn và tìm tài liệu…". Khi có token: "Đang viết câu trả lời…". Xong (chỉ `.sr-only`): "Đã trả lời xong, N nguồn." (hoặc "Đã trả lời xong.") | loading -> streaming -> success | Không bao giờ thấy bong bóng assistant trống; trình đọc màn hình đọc đúng 3 thông báo trên, không đọc từng token (log `aria-busy=true` khi stream, `false` khi xong) |
| K-04 | Chat, nút Dừng và Thử lại (V-09) | Không dừng/thử lại | Dùng `AbortController` cho `fetch` stream. Khi `busy`, nút gửi `↑` đổi thành nút Dừng (`type="button"`, cùng vị trí, `aria-label`). Dừng giữ phần đã viết, gắn nhãn đã dừng. Với lỗi: thêm nút "Thử lại" trong bong bóng lỗi gửi lại câu hỏi gần nhất | Nút: "Dừng" (aria-label "Dừng câu trả lời"). Nhãn sau dừng: "Đã dừng trả lời." Nút lỗi: "Thử lại" | streaming, stopped, error | Bấm Dừng: request bị hủy, `busy=false`, focus về ô nhập, bong bóng giữ phần đã viết + nhãn; "Thử lại" gửi lại và thay bong bóng lỗi |
| K-05 | Lỗi mạng/JSON (V-03) | Lỗi kỹ thuật | Tạo hàm `friendlyError(e, status?)`: `TypeError`/"Failed to fetch" -> thông điệp mạng; HTTP 5xx hoặc JSON hỏng -> thông điệp máy chủ; 4xx có `detail` tiếng Việt -> hiển thị `detail`; `detail` khác -> thông điệp chung. Dùng cho cả `postApi` và `sendChat`. Không bao giờ hiện `e.message` thô | Mạng: "Không kết nối được tới máy chủ. Hãy kiểm tra kết nối rồi bấm Thử lại." Máy chủ: "Hệ thống đang gặp sự cố. Vui lòng thử lại sau ít phút." Gián đoạn giữa chừng: "Kết nối bị gián đoạn. Phần đã nhận được giữ nguyên, bấm Thử lại để hỏi lại." Chung: "Chưa xử lý được yêu cầu. Vui lòng thử lại." | error | Tắt API rồi gửi chat/form: thấy thông điệp tiếng Việt tương ứng, có hướng khắc phục; không còn chuỗi "Failed to fetch"/"Unexpected token" |
| K-06 | Chat, tin nhắn cảnh báo cấp cứu (V-06) | Hiển thị như thường | Khi trace chứa bước `Blocked` (regex `/Blocked/i`) hoặc `turn.blocked`: bong bóng kiểu `.chat-safety` (viền trái 4px `#b4572a`, nền `#fff4ee`, có biểu tượng chữ "Cảnh báo an toàn" ở đầu, không chỉ màu). Giữ nguyên `content` từ API nhưng hiển thị `text-transform: none`; thêm nút gọi `tel:115` | Đầu bong bóng (in đậm): "Cảnh báo an toàn". Nút: "Gọi 115" (`<a href="tel:115">`). Dưới trace: "Hệ thống dừng tại Rule Agent, không tìm tài liệu." | success (blocked) | Gửi "Tôi bị đau ngực dữ dội, khó thở": bong bóng có nhãn "Cảnh báo an toàn" và liên kết "Gọi 115"; trace dừng sau Rule Agent; tương phản chữ ≥ 4.5:1 |
| K-07 | Chat, auto-scroll (V-08) | Giật, cướp cuộn | Chỉ cuộn khi người dùng đang gần đáy (`scrollHeight - scrollTop - clientHeight < 80`). Dùng `behavior: 'auto'` khi `matchMedia('(prefers-reduced-motion: reduce)').matches`, ngược lại `'smooth'`; chỉ cuộn khi thêm tin nhắn hoặc kết thúc, không cuộn mỗi token | không có copy | streaming | Cuộn lên giữa lúc stream không bị kéo xuống; bật Reduce Motion thì không có hoạt ảnh |
| K-08 | Chat, nhắc y tế mỗi câu trả lời (V-15) | Thiếu nhắc | Dưới `.chat-text` của mỗi câu assistant không lỗi, không blocked, thêm một dòng `<small class="chat-disclaimer">` màu `#4f5f56`, ≥ 12px | "Thông tin tham khảo, không thay thế tư vấn của bác sĩ." | success | Có ở mọi câu trả lời thành công; không có ở câu lỗi và câu cảnh báo an toàn |
| K-09 | Header trạng thái (V-12) | Mơ hồ | Dùng `health.services`: nếu thiếu dịch vụ liệt kê tên. Khi chưa tải xong hiện "Đang kiểm tra…". Khi Ollama sai: vô hiệu hóa gửi chat kèm lý do trong `#chat-hint` | Chưa tải: "Đang kiểm tra dịch vụ…". Đủ: "Dịch vụ: Trực tuyến". Thiếu: "Chưa sẵn sàng: Neo4j" / "Chưa sẵn sàng: mô hình ngôn ngữ (Ollama)" / "Chưa sẵn sàng: Neo4j, mô hình ngôn ngữ". Mất API: "Không kết nối được máy chủ". Hint chat khi tắt: "Chưa gửi được vì mô hình ngôn ngữ chưa chạy. Hãy khởi động Ollama rồi tải lại trang." | loading, partial, offline | Giả lập `health` 4 trường hợp, text đúng; `role="status"` chỉ ở header, nút gửi chat disabled khi `ollama=false` |
| K-10 | Kết quả dự đoán (V-04) | "Lớp 0/1" + "/ 1" | Thay khối `score-card`: thêm banner trên cùng; số hiển thị bằng `toLocaleString('vi-VN',{minimumFractionDigits:3})` (vd "0,874"), bỏ " / 1"; thay badge "Lớp" bằng câu; giữ `answer.meaning` bên dưới. Đặt cảnh báo phi lâm sàng ở trên điểm, không chỉ ở cuối | Banner: "Kết quả thử nghiệm trên dữ liệu khảo sát, không phải chẩn đoán." Nhãn số: "Điểm của mô hình (0 đến 1)". Lớp 1: "Mô hình xếp vào nhóm giống người từng được chẩn đoán đái tháo đường (ngưỡng 0,5)". Lớp 0: "Mô hình xếp vào nhóm ít giống người từng được chẩn đoán đái tháo đường (ngưỡng 0,5)". Hàng cuối: "Điểm này không phải xác suất bạn mắc bệnh. Hãy hỏi bác sĩ nếu bạn lo lắng." (`threshold` thay "0,5" theo dữ liệu) | success | Với score 0.874 thấy "0,874"; không còn chữ "Lớp" hay "/ 1"; banner nằm trước số; ngưỡng lấy từ `answer.threshold` |
| K-11 | Form 15 chỉ số và form chung (V-13) | Thiếu hướng dẫn, nhóm | Chia 15 chỉ số thành `<fieldset><legend>` 4 nhóm: "Thông tin chung" (giới tính, tuổi), "Cơ thể" (cân nặng, chiều cao, vòng eo), "Huyết áp", "Xét nghiệm máu". Thêm `<small class="field-hint">` cho mỗi chỉ số y khoa; thêm mô tả khoảng hợp lệ trong hint; thêm đoạn đầu form. Đổi placeholder `select`. Khi submit lỗi (BMI) thêm `aria-describedby` tới `.error` và đưa focus vào `.error` | Đầu form: "Điền số từ phiếu xét nghiệm của bạn hoặc số giả lập. Mọi ô đều bắt buộc." Select placeholder: "Chọn…" (disabled option). Nhãn giới tính: "Giới tính (theo khảo sát NHANES)". Hints: HbA1c "Đường huyết trung bình 2-3 tháng, ghi trên phiếu xét nghiệm. Từ 3 đến 20 %"; Glucose "Đo khi nhịn ăn ít nhất 8 giờ. Từ 40 đến 500 mg/dL"; ALT "Men gan, từ 1 đến 1000 U/L"; Creatinine "Chỉ số chức năng thận, từ 0,1 đến 15 mg/dL"; Triglyceride "Mỡ máu, từ 10 đến 3000 mg/dL"; các ô còn lại "Từ min đến max đơn vị" lấy từ mảng | form, error | Mỗi nhóm có legend; trình đọc đọc legend + nhãn; submit thiếu ô: focus về ô đầu tiên lỗi (hành vi HTML gốc OK) và `.error` hiển thị thông điệp BMI bằng tiếng Việt như hiện tại |
| K-12 | Kết quả (aside), live region và focus (V-16) | Đọc cả aside | Bỏ `aria-live` khỏi `<aside>`; thêm một `<p role="status" class="sr-only">` cập nhật khi có kết quả; sau khi có kết quả chuyển focus vào `<h2>` của aside (`tabIndex={-1}`) và cuộn vào tầm nhìn (`block:'nearest'`) | Status: "Đã có kết quả." / "Đã có đề xuất chủ đề." | success | Mobile 390px: gửi form thì thấy kết quả không cần cuộn tay; trình đọc đọc "Đã có kết quả." rồi tiêu đề, không đọc cả khối |
| K-13 | Tab RL kết quả (V-14) | Thiếu giải thích | Với response `/api/learning`: hiện "Chủ đề nên học tiếp:" + `topic` làm `<h2>`; nếu `policy_overridden` thêm dòng giải thích; bỏ `answer.disclaimer` ở tab RL và dùng chuỗi cố định; giữ `message` khi `status==='completed'` | "Chủ đề nên học tiếp: {topic}". Overridden: "Luật an toàn đã điều chỉnh đề xuất của mô hình DQN." Mặc định disclaimer RL: "Đây là mô phỏng học tập, không phải chỉ định điều trị." Mô tả dưới nút: "DQN là mô hình học tăng cường: nó chọn chủ đề giúp người học giả lập tiến bộ nhiều nhất." | success, completed | Kết quả thật `{"topic":"Tổng quan về tiểu đường"}` hiện "Chủ đề nên học tiếp: Tổng quan về tiểu đường"; bỏ chọn hết hiện h2 "Tất cả các chủ đề đã hoàn thành" và message; không còn chữ "mô phỏng ... mô phỏng" |
| K-14 | Tab Kiến trúc bố cục (V-05, V-21) | Không khớp bảng | Viết lại `Architecture()` theo mục 5: 3 lớp, mỗi lớp `<section aria-labelledby>` với `<h2>`. Chuyển "Reinforcement Learning + Rule" ra khỏi lớp dữ liệu: tách thành hai hộp trong lớp tác tử ("Rule Agent" và "Learning Agent"). Thêm hộp "Web, sách" mũi tên "tạo" tới Neo4j KB; thêm hộp "Deep Learning (CNN 1D / MLP)" giữa DB và Prediction Agent; hộp cuối đổi tên. Ghi chú mũi tên "Rule duyệt xong mới tới Knowledge" bằng chữ trong hộp Rule. Giữ `aria-hidden` cho mũi tên trang trí. Thay `chat-note` bên dưới bằng chú giải màu | Lớp 1: "Dữ liệu và tri thức"; hộp "Dữ liệu có sẵn" (UCI · BRFSS · NHANES); hộp "Web, sách, hướng dẫn" (WHO · ADA · CDC · NIDDK · Bộ Y tế) "tạo" -> "Neo4j KB": "Tài liệu có vector và đồ thị thực thể". Lớp 2: "Các tác tử"; "Prediction Agent": "Học sâu (CNN 1D, MLP) dự đoán / phân loại từ chỉ số"; "Knowledge Agent": "Tìm đoạn tài liệu gần nghĩa (RAG)"; "Knowledge Graph Agent": "Tra quan hệ, ngưỡng, tài liệu gốc trong đồ thị"; "Rule Agent": "Chặn cấp cứu, hỏi liều thuốc, lộ thông tin cá nhân, prompt injection trước khi tra cứu"; "Learning Agent": "Học tăng cường (DQN) + luật bảo vệ, chọn chủ đề nên học tiếp"; "Conversation Agent": "Trả lời lời chào, giữ ngữ cảnh". Lớp 3: "Điều phối và phản hồi"; "Coordinator (LangGraph)": "Định tuyến theo trạng thái"; "Response Agent (LLM)": "Viết câu trả lời chỉ từ nguồn, có trích dẫn [n]"; "Tư vấn / trợ giúp": "Đầu ra cho người dùng, kèm cảnh báo phi lâm sàng". Chú giải: "Màu viền trái của từng tác tử giống màu thẻ trong 'Luồng xử lý' ở tab Hỏi đáp." | tĩnh | 100% thành phần bảng ở mục 5 có mặt; Rule và Learning không nằm ở lớp dữ liệu; không `h1 -> h3`; ở 390px các lớp xếp dọc, không cuộn ngang, mũi tên đổi hướng |
| K-15 | Tab Kiến trúc, "Một câu hỏi đi qua đâu" (H10) | Thiếu giải thích luồng | Thêm `<section>` có `<h2>` và `<ol>` 5 mục dưới các lớp | h2: "Một câu hỏi đi qua đâu". Bước: "1. Coordinator nhận câu hỏi và chuyển cho Rule Agent." "2. Rule Agent kiểm tra an toàn. Nếu nguy hiểm thì dừng và đưa cảnh báo." "3. Knowledge Agent tìm tài liệu gần nghĩa." "4. Knowledge Graph Agent tra thêm quan hệ và tài liệu gốc trong Neo4j." "5. Response Agent viết câu trả lời có trích dẫn, kèm nguồn và các bước đã chạy." | tĩnh | Danh sách có thứ tự, đúng 5 bước, khớp trace thật ở mục 0 |
| K-16 | Trang chủ (V-15, V-23) | Overclaim, thiếu KG và liên kết | Đổi eyebrow hero; sửa đoạn intro; thêm thẻ thứ 4 "Kiến trúc hệ thống" (`reset('arch')`); đổi mô tả thẻ "Hỏi đáp có nguồn" | Eyebrow: "KIẾN THỨC THAM KHẢO TỪ NGUỒN UY TÍN, DÀNH CHO HỌC TẬP". Intro: "Hệ thống gồm các tác tử: Prediction, Knowledge, Knowledge Graph, Rule, Learning và Response, do Coordinator điều phối." Thẻ 04: tiêu đề "Kiến trúc hệ thống", mô tả "Xem các tác tử và dữ liệu nối với nhau như thế nào." Thẻ 02: "Đặt câu hỏi, xem nguồn đi kèm và các bước hệ thống đã xử lý." | tĩnh | Không còn chữ "NGUỒN CHÍNH THỨC"; có 4 thẻ, thẻ 04 mở tab Kiến trúc; mô tả tác tử có Knowledge Graph |
| K-17 | Skip link, glyph, heading, nav (V-16, V-19, V-21, V-24) | a11y nền | Thêm `<a class="skip-link" href="#main">` đầu `.shell`, hiện khi focus; `id="main"` + `tabIndex={-1}` ở `<main>`. Thêm `aria-hidden="true"` cho mọi `✳` trang trí. Với nav ≤800px thêm bóng mờ (mask) cuối dòng để biết còn mục | Skip link: "Bỏ qua điều hướng, đến nội dung chính" | mọi | Tab lần 1 hiện skip link, Enter chuyển focus vào main; trình đọc không đọc "dấu hoa thị"; ở 390px thấy dấu hiệu cuộn tiếp (chưa kiểm) |
| K-18 | Tương phản chữ nhỏ (V-11) | < 4.5:1 | `nav button` màu `#4a5f54`; `.brand small` `#566b60`, size 9px, spacing giữ; `.chat-trace` xem K-02. Kiểm lại bằng công cụ trên nền thật (header). Đo mọi chữ ≤ 13px trên 390px | không có copy | mọi | Mọi cặp chữ/nền ≥ 4.5:1 (nút nav, brand small, trace, hint); báo số đo kèm bằng chứng |
| K-19 | Form, đổi bộ dữ liệu (V-17, V-18) | Mất dữ liệu, nhãn gần nghĩa | Đổi nhãn tab; khi `values` đã có dữ liệu và đổi tab, hiện dòng thông báo trong 1 `role="status"`; nhóm tab đổi sang `role="radiogroup"` + `role="radio"` + `aria-checked` (phím mũi tên) hoặc giữ `aria-pressed` nếu muốn tối giản | Nhãn: "NHANES đầy đủ (15 chỉ số)"; "NHANES rút gọn (4 chỉ số)"; "BRFSS (khảo sát lối sống)"; "UCI (triệu chứng)". Thông báo: "Đã chuyển bộ dữ liệu, các ô đã nhập được xóa." | form | Nhãn mới hiển thị; đổi tab sau khi đã nhập thì có thông báo; kiểm Tab/phím mũi tên theo lựa chọn |
| K-20 | Ô nhập chat (V-22) | Cắt ký tự, chiều cao cố định | Hiện bộ đếm khi ≥ 1300 ký tự; đổi `.chat-messages` `height` thành `min(60dvh, 470px)` (≥360px), đảm bảo ô nhập thấy được khi bàn phím ảo mở (kiểm bằng thiết bị thật) | Bộ đếm (`aria-live="off"`, chỉ hiện chữ): "{n}/1500 ký tự" | chat | Ở 390x844 composer luôn nằm trong khung nhìn; bộ đếm xuất hiện đúng ngưỡng |
| K-21 | Nguồn (V-20) | Tiêu đề lặp | Trong `SourceList`, bỏ tiền tố `Đồ thị tri thức Neo4j:` (và khoảng trắng) khỏi tiêu đề khi `cls==='graph'`; nếu hai nguồn cùng URL, giữ cả hai nhưng nối "(cùng liên kết)" vào `small` nguồn thứ hai | "Cùng liên kết với nguồn [n]" | success | Tiêu đề nguồn đồ thị chỉ còn "Tự kiểm tra bàn chân mỗi ngày, Loét bàn chân, nguy cơ cắt cụt"; badge vẫn ghi "Đồ thị tri thức Neo4j" |

Số mục handoff: **21** (K-01 đến K-21). Thứ tự ưu tiên demo: K-01, K-03, K-05, K-10, K-14, K-06 (mức 3) trước; K-02, K-04, K-07..K-09, K-11..K-13, K-15, K-16, K-18 (mức 2) tiếp; còn lại mức 1.

## 7. Microcopy: nguyên tắc đã áp dụng ở bảng trên

- Câu ngắn, chủ động, nói việc người dùng làm tiếp theo. Tên riêng tác tử giữ nguyên (Rule Agent...), phần mô tả dùng "tác tử" thay "agent".
- Không dùng "Lớp 0/1", "Score", "Approved". Số dùng dấu phẩy thập phân vi-VN.
- Nhắc y tế đúng mức: một dòng cố định dưới mỗi câu trả lời thành công; banner ở kết quả dự đoán; cấp cứu có "Gọi 115". Không lặp cảnh báo dài ở mọi nơi.
- Lỗi: nói gì xảy ra + làm gì tiếp, không lộ chi tiết kỹ thuật.

## 8. Việc ngoài phạm vi frontend, báo Atlas

- Chat: nguồn "Sức khỏe tinh thần và căng thẳng..." xuất hiện cho câu hỏi chăm sóc bàn chân (ngưỡng truy xuất cosine 0,875 vẫn lọt?). Cân nhắc Rex/Pollux xem lại ngưỡng hoặc xếp hạng.
- Backend `disclaimer` của `/api/learning` lặp từ ("Mô phỏng giáo dục mô phỏng"); frontend đã đề xuất tạm thời dùng chuỗi cố định (K-13); nên sửa tận gốc.
- Bước trace trùng ("Rule Agent" rồi "Rule Agent (Approved)") là do backend; K-01 xử lý ở hiển thị.

## 9. Việc Hawk/Kit cần xác nhận khi chạy thật (chưa kiểm được bằng mắt)

1. 390px: nav cuộn ngang, pipeline xếp dọc, các lớp kiến trúc, chiều cao chat khi bàn phím ảo mở.
2. Tab bằng bàn phím qua header, chat, form; skip link; focus sau khi có kết quả.
3. Trình đọc màn hình (VoiceOver): thông báo khi stream, thông báo hoàn tất, đọc trace.
4. Đo tương phản bằng công cụ trên nền thực (nav, brand small).
5. Thử các trạng thái lỗi: tắt API, tắt Ollama (health partial), proxy trả HTML.
