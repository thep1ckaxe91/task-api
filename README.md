# Tasks API

RESTful API quản lý công việc (Tasks) được xây dựng bằng Python Flask, sử dụng OpenAPI 3.0.3 để đặc tả API và Swagger UI để thực hiện kiểm thử trực tiếp.

## 1. Installation & Running

**Yêu cầu:** Python 3.12 và Git.

Clone repository:

```bash
git clone https://github.com/thep1ckaxe91/task-api.git
cd task-api
```

Tạo và kích hoạt môi trường ảo trên Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Cài đặt các thư viện:

```powershell
python -m pip install -r requirements.txt
```

Khởi chạy Flask trên localhost:

```powershell
python -m flask --app app run --host 127.0.0.1 --port 5000 --no-debugger --no-reload
```

Truy cập:

- Swagger UI: http://localhost:5000/docs
- OpenAPI JSON: http://localhost:5000/openapi.json

Swagger UI hỗ trợ sử dụng **Try it out** để gửi request và kiểm tra response trực tiếp.

## 2. API Endpoints

Hệ thống cung cấp 5 operations trên resource `Task`.

| Method | Endpoint | Chức năng | HTTP Status |
|---|---|---|---|
| GET | `/tasks` | Lấy danh sách task | 200 |
| POST | `/tasks` | Tạo task mới | 201, 400 |
| GET | `/tasks/{id}` | Lấy chi tiết task | 200, 404 |
| PATCH | `/tasks/{id}` | Cập nhật một phần task | 200, 400, 404 |
| DELETE | `/tasks/{id}` | Xóa task | 204, 404 |

Task gồm các trường:

- `id`: Integer, được server tự động sinh.
- `title`: String không rỗng, bắt buộc khi tạo.
- `description`: String, mặc định `""`.
- `completed`: Boolean, mặc định `false`.

Ý nghĩa các HTTP status codes:

- **200 OK:** Truy vấn hoặc cập nhật thành công.
- **201 Created:** Tạo task mới thành công, trả về task và header `Location`.
- **204 No Content:** Xóa thành công, response không có body.
- **400 Bad Request:** Request không hợp lệ, thiếu trường bắt buộc hoặc sai kiểu dữ liệu.
- **404 Not Found:** Task không tồn tại.

Đặc tả chi tiết được lưu trong file `openapi.yaml`.

## 3. Design Decisions

### 3.1. PATCH vs PUT

**Quyết định:** Sử dụng `PATCH` để cập nhật một phần task thay vì `PUT`.

`PUT` thường được dùng để thay thế toàn bộ biểu diễn của một resource, còn `PATCH` áp dụng các thay đổi được chỉ định trong request.

Trong Tasks API, người dùng thường chỉ cần thay đổi một thuộc tính, chẳng hạn đánh dấu hoàn thành:

```json
{
  "completed": true
}
```

Sử dụng PATCH giúp client không phải gửi lại `title` và `description`. Các trường không được gửi vẫn giữ nguyên giá trị trước đó.

Trong `app.py`, việc cập nhật được thực hiện bằng `task.update(body)` sau khi request đã được kiểm tra hợp lệ.

**Ưu điểm:**

- Giảm dữ liệu cần gửi khi chỉ sửa một vài trường.
- Tránh nguy cơ ghi đè các trường không cần thay đổi.
- Phù hợp với thao tác chỉnh sửa trạng thái công việc.

**Đánh đổi:** PATCH cần validation chặt chẽ để chỉ cho phép cập nhật các trường hợp lệ. PUT có tính idempotent theo ngữ nghĩa HTTP, trong khi PATCH không mặc nhiên bảo đảm tính chất này. Tuy nhiên, cách cập nhật bằng phép gán giá trị các trường hiện tại vẫn có thể idempotent.

**Kết luận:** PATCH phù hợp hơn với yêu cầu cập nhật từng phần của Tasks API.

### 3.2. In-memory Dictionary vs Database

**Quyết định:** Sử dụng in-memory dictionary thay vì database.

Hệ thống lưu task bằng dictionary Python:

```python
tasks: dict[int, dict] = {}
```

Mỗi task được lưu với khóa là `id`, được tự động sinh bằng `itertools.count(1)`.

**Ưu điểm:**

- Không cần cài đặt hoặc cấu hình database.
- Code đơn giản, dễ triển khai và kiểm thử.
- Truy xuất dữ liệu trong bộ nhớ có độ trễ thấp.
- Phù hợp với mục tiêu minh họa OpenAPI và CRUD.

**Hạn chế:**

- Dữ liệu bị mất khi process khởi động lại.
- Không có cơ chế lưu trữ bền vững.
- Nhiều process hoặc worker không tự động chia sẻ dữ liệu.
- Chưa phù hợp với hệ thống nhiều người dùng đồng thời hoặc cần mở rộng quy mô.

Database như SQLite hoặc PostgreSQL hỗ trợ lưu trữ lâu dài và cung cấp những cơ chế quản lý dữ liệu phù hợp hơn cho ứng dụng thực tế, nhưng sẽ làm tăng độ phức tạp triển khai.

**Kết luận:** In-memory dictionary là lựa chọn hợp lý cho bài tập Spec-First API quy mô nhỏ. Khi cần triển khai thực tế, nên chuyển sang database để bảo đảm tính bền vững và khả năng mở rộng.

## 4. Screenshots

Các API đã được kiểm thử thủ công bằng chức năng **Try it out** trên Swagger UI. Cả 10 test case trong kế hoạch kiểm thử đều đạt, bao gồm các trường hợp thành công và lỗi 400, 404.

**Giao diện Swagger UI:**

[01 — Swagger UI](screenshots/01-swagger-ui.png)

**Các thao tác CRUD thành công:**

[GET /tasks — 200](screenshots/02-get-tasks-200.png) · [POST /tasks — 201](screenshots/03-post-task-201.png) · [GET /tasks/{id} — 200](screenshots/04-get-task-200.png) · [PATCH /tasks/{id} — 200](screenshots/05-patch-task-200.png) · [DELETE /tasks/{id} — 204](screenshots/06-delete-task-204.png)

**Các trường hợp lỗi:**

[POST thiếu title — 400](screenshots/07-post-missing-title-400.png) · [PATCH sai kiểu dữ liệu — 400](screenshots/08-patch-invalid-type-400.png) · [GET không tồn tại — 404](screenshots/09-get-not-found-404.png) · [PATCH không tồn tại — 404](screenshots/10-patch-not-found-404.png) · [DELETE không tồn tại — 404](screenshots/11-delete-not-found-404.png)

**Minh chứng kiểm thử có sẵn của nhóm:**

<p align="center">
    <img src=".github/assets/test-log-1.png" width="100%" alt="Test Log 1">
    <img src=".github/assets/test-log-2.png" width="100%" alt="Test Log 2">
</p>