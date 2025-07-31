# Hướng dẫn setup Google Drive cho file download

## Bước 1: Upload file lên Google Drive

1. Truy cập [Google Drive](https://drive.google.com)
2. Upload file `Mahika.exe` của bạn
3. Right-click vào file → "Get link"
4. Chọn "Anyone with the link" có thể xem
5. Copy link

## Bước 2: Chuyển đổi Google Drive link

**Link gốc từ Google Drive:**

```
https://drive.google.com/file/d/1ABC123DEF456XYZ/view?usp=sharing
```

**Chuyển thành direct download link:**

```
https://drive.google.com/uc?export=download&id=1ABC123DEF456XYZ
```

Chỉ cần thay `1ABC123DEF456XYZ` bằng FILE_ID thực tế của bạn.

## Bước 3: Cập nhật .env

```properties
DOWNLOAD_FILE_URL=https://drive.google.com/uc?export=download&id=YOUR_REAL_FILE_ID
DOWNLOAD_FILE_NAME=Mahika.exe
```

## Bước 4: Deploy lên Railway

1. **Tạo Railway project:**

   ```bash
   railway login
   railway init
   railway add mysql
   ```

2. **Deploy:**

   ```bash
   railway up
   ```

3. **Set environment variables:**
   - Copy tất cả variables từ `.env` vào Railway dashboard
   - Đặc biệt quan trọng: `DOWNLOAD_FILE_URL`

## Ưu điểm của Google Drive:

✅ **Không tốn dung lượng deploy**
✅ **Download nhanh, ổn định**
✅ **Dễ cập nhật file mới**
✅ **Miễn phí**
✅ **Không giới hạn bandwidth**

## Lưu ý:

- File phải public (Anyone with the link can view)
- Dùng direct download link (`uc?export=download&id=`)
- Test link trước khi deploy
- Có thể thay đổi file mà không cần redeploy

## Test local:

1. Cập nhật `DOWNLOAD_FILE_URL` trong `.env`
2. Restart Flask app
3. Login → Dashboard → Download
4. Phải redirect đến Google Drive và tự động download

## Backup plan:

Nếu Google Drive có vấn đề, bạn vẫn có thể:

- Bỏ `DOWNLOAD_FILE_URL` khỏi .env
- App sẽ fallback về local file trong `app/static/downloads/`
