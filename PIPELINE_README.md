# Daily Data Pipeline

## Tổng quan

Pipeline tự động cập nhật dữ liệu hàng ngày cho hệ thống trading bot, chạy vào lúc 7:00 PM hàng ngày.

## Các bước trong Pipeline

1. **Balance Update** - Cập nhật số dư tài khoản
2. **Deals Update** - Cập nhật giao dịch mới nhất  
3. **Universe Update** - Cập nhật danh sách cổ phiếu hàng tháng
4. **Weights Update** - Cập nhật trọng số tối ưu
5. **Notifications** - Gửi báo cáo qua Telegram

## Cách chạy

### 1. Chạy Pipeline Service (Tự động hàng ngày)

```bash
# Chạy service pipeline tự động
python run_daily_pipeline.py
```

Service sẽ:
- Chạy liên tục 24/7
- Tự động thực hiện pipeline lúc 7:00 PM mỗi ngày
- Gửi thông báo qua Telegram khi hoàn thành hoặc có lỗi

### 2. Chạy Pipeline thủ công qua API

```bash
# Cập nhật balance data
POST /api/portfolio/data/update-balance

# Cập nhật deals data  
POST /api/portfolio/data/update-deals

# Chạy toàn bộ pipeline
POST /api/portfolio/pipeline/run-manual
```

### 3. Chạy từng service riêng lẻ

```python
# Balance Service
from backend.modules.portfolio.services.balance_service import BalanceService
result = await BalanceService.update_newest_data_all_daily()

# Deals Service  
from backend.modules.portfolio.services.deals_service import DealsService
result = await DealsService.update_newest_data_all_daily()
```

## Monitoring

### Logs
- Tất cả hoạt động được ghi log chi tiết
- Kiểm tra log để theo dõi trạng thái pipeline

### Telegram Notifications
- Thông báo tóm tắt kết quả pipeline
- Cảnh báo khi có lỗi xảy ra
- Thống kê chi tiết từng bước

### API Response
```json
{
  "success": true,
  "start_time": "2024-01-15T19:00:00",
  "end_time": "2024-01-15T19:05:30", 
  "total_duration": 330.5,
  "steps": {
    "balance_update": {
      "success": true,
      "duration_seconds": 45.2,
      "result": {
        "updated_accounts": 5,
        "failed_accounts": 0
      }
    },
    "deals_update": {
      "success": true, 
      "duration_seconds": 67.8,
      "result": {
        "updated_accounts": 5,
        "total_deals": 23
      }
    }
  }
}
```

## Troubleshooting

### Lỗi thường gặp

1. **DNSE API Connection Timeout**
   - Kiểm tra kết nối mạng
   - Thử lại sau vài phút

2. **Database Connection Error**
   - Kiểm tra SQL Server connection
   - Xác thực credentials

3. **Authentication Failed**
   - Kiểm tra thông tin tài khoản trading
   - Cập nhật password nếu cần

### Khắc phục

1. **Restart Pipeline Service**
   ```bash
   # Stop current service (Ctrl+C)
   # Restart
   python run_daily_pipeline.py
   ```

2. **Manual Run for Recovery**
   ```bash
   # Chạy pipeline thủ công để recovery
   curl -X POST http://localhost:8000/api/portfolio/pipeline/run-manual
   ```

3. **Individual Service Recovery**
   ```bash
   # Chỉ cập nhật balance
   curl -X POST http://localhost:8000/api/portfolio/data/update-balance
   
   # Chỉ cập nhật deals
   curl -X POST http://localhost:8000/api/portfolio/data/update-deals
   ```

## Cấu hình

### Thời gian chạy
Mặc định: 7:00 PM hàng ngày (timezone Vietnam)

Để thay đổi, sửa trong `daily_data_pipeline.py`:
```python
PIPELINE_TIME = time(19, 0)  # 7:00 PM
```

### Retry Logic
- Pipeline sẽ tiếp tục chạy các bước khác nếu 1 bước fail
- Thông báo lỗi qua Telegram
- Auto-retry scheduler sau 5 phút nếu có lỗi

## Dependencies

- DNSE API connection
- SQL Server database  
- Redis cache
- Telegram Bot API
- Active trading accounts

## Performance

- Balance Update: ~30-60 giây
- Deals Update: ~45-90 giây  
- Universe Update: ~60-120 giây
- Weights Update: ~90-180 giây
- Notifications: ~10-30 giây

**Tổng thời gian:** ~4-8 phút tùy số lượng accounts
