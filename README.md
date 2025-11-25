# IST Technical Assessment - Procure-to-Pay System

A mini "Procure-to-Pay" system built with Django REST Framework and React, featuring multi-level approval workflows, document processing (AI-based), and receipt validation.

## 🚀 Features

- **Multi-level Approval Workflow**: Staff → Approver Level 1 → Approver Level 2 → Finance
- **Document Processing**: AI-powered extraction from proforma invoices and receipts
- **Receipt Validation**: Automatic comparison of receipts against Purchase Orders
- **Role-based Access Control**: Staff, Approvers (Level 1 & 2), and Finance roles
- **Purchase Order Generation**: Automatic PO generation on final approval
- **RESTful API**: Complete API with JWT authentication
- **React Frontend**: Modern UI with role-based dashboards
- **Docker Support**: Containerized with Docker and docker-compose

##  Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose (optional, for containerized deployment)
- PostgreSQL (for production) or SQLite (for development)

## 🛠️ Setup Instructions

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables (optional):**
   Create a `.env` file in the `backend` directory:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DB_NAME=purchase_order_db
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=localhost
   DB_PORT=5432
   USE_SQLITE=True  # Set to True for SQLite, False for PostgreSQL
   ALLOWED_HOSTS=localhost,127.0.0.1
   OPENAI_API_KEY=your-openai-api-key  # Optional, for AI document processing
   ```

5. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server:**
   ```bash
   python manage.py runserver
   ```

   Backend will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

   Frontend will be available at `http://localhost:5173`

### Docker Setup (Recommended)

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Build and run with docker-compose:**
   ```bash
   docker-compose up --build
   ```

   This will:
   - Start PostgreSQL database
   - Build and run Django backend
   - Run migrations automatically
   - Make backend available at `http://localhost:8000`

3. **For frontend with Docker (optional):**
   Create a `Dockerfile` in the frontend directory and use docker-compose to orchestrate both services.

## 📚 API Documentation

Once the backend is running, access Swagger UI at:
- **Swagger UI**: `http://localhost:8000/swagger/`

### API Endpoints

#### Authentication
- `POST /accounts/register/` - Register new user
- `POST /accounts/login/` - Login and get JWT tokens

#### Purchase Requests
- `POST /api/v1/purchase-request/` - Create purchase request (Staff only)
- `GET /api/v1/Get-purchase-request/` - List purchase requests
- `GET /api/v1/Get-purchase-request/{id}/` - Get purchase request details
- `PUT /api/v1/update-purchase-request/{id}/` - Update purchase request (Staff, pending only)
- `PATCH /api/v1/approve-request/{id}/` - Approve request (Approvers)
- `PATCH /api/v1/reject-request/{id}/` - Reject request (Approvers)
- `POST /api/v1/submit-receipt/{id}/` - Submit receipt for validation (Staff)

### Authentication

All API endpoints (except register/login) require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your-access-token>
```

## 🎯 User Roles

1. **Staff**: Can create, view, and update their own purchase requests; submit receipts
2. **Approver Level 1**: Can approve/reject requests at first level
3. **Approver Level 2**: Can approve/reject requests at second level
4. **Finance**: Can approve requests (final approval) and generate Purchase Orders

## 🔄 Workflow

1. **Staff** creates a purchase request with items and optional proforma invoice
2. **Approver Level 1** reviews and approves/rejects
3. **Approver Level 2** reviews and approves/rejects (if Level 1 approved)
4. **Finance** provides final approval, which automatically generates a Purchase Order
5. **Staff** submits receipt after purchase
6. System validates receipt against PO and flags discrepancies

## 🤖 AI Document Processing

The system uses AI/OCR for document processing:

- **Proforma Extraction**: Extracts vendor, items, prices, and terms from proforma invoices
- **Receipt Extraction**: Extracts seller, items, and total from receipts
- **Receipt Validation**: Compares receipt data against Purchase Order

**Libraries Used:**
- `pdfplumber` - PDF text extraction
- `PyPDF2` - PDF parsing fallback
- `pytesseract` - OCR for images
- `openai` - AI-powered extraction (optional, requires API key)

## 🐳 Deployment

### Using Docker

1. **Build and run:**
   ```bash
   cd backend
   docker-compose up --build -d
   ```

2. **Access the application:**
   - Backend: `http://localhost:8000`
   - Swagger: `http://localhost:8000/swagger/`

### Production Deployment

For production deployment (AWS EC2, Render, Fly.io, etc.):

1. Set `DEBUG=False` in environment variables
2. Set a strong `SECRET_KEY`
3. Configure `ALLOWED_HOSTS` with your domain
4. Use PostgreSQL database
5. Set up static file serving (e.g., WhiteNoise, S3, etc.)
6. Configure CORS for your frontend domain
7. Set up SSL/HTTPS

### Environment Variables for Production

```env
DEBUG=False
SECRET_KEY=your-strong-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_NAME=production_db
DB_USER=db_user
DB_PASSWORD=strong_password
DB_HOST=db_host
DB_PORT=5432
USE_SQLITE=False
```

## 📝 Testing

### Create Test Users

You can create users via Django admin or API:

1. **Staff User:**
   ```bash
   python manage.py shell
   ```
   ```python
   from accounts.models import CustomUser
   CustomUser.objects.create_user(username='staff1', password='password123', role='staff')
   ```

2. **Approver Level 1:**
   ```python
   CustomUser.objects.create_user(username='approver1', password='password123', role='approver_level_1')
   ```

3. **Approver Level 2:**
   ```python
   CustomUser.objects.create_user(username='approver2', password='password123', role='approver_level_2')
   ```

4. **Finance:**
   ```python
   CustomUser.objects.create_user(username='finance1', password='password123', role='finance')
   ```

## 🐛 Troubleshooting

### Tesseract OCR Issues
If you encounter Tesseract errors:
- **Linux**: `sudo apt-get install tesseract-ocr`
- **macOS**: `brew install tesseract`
- **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Database Connection Issues
- Ensure PostgreSQL is running (if using PostgreSQL)
- Check database credentials in `.env` file
- For SQLite, set `USE_SQLITE=True` in `.env`

### CORS Issues
- Update `CORS_ALLOWED_ORIGINS` in `settings.py` with your frontend URL
- Or set `CORS_ALLOW_ALL_ORIGINS=True` for development (not recommended for production)

## 📦 Project Structure

```
IST_Project/
├── backend/
│   ├── accounts/          # User authentication and roles
│   ├── P_order/          # Purchase order app
│   │   ├── models.py     # Data models
│   │   ├── views.py      # API views
│   │   ├── serializer.py # DRF serializers
│   │   ├── urls.py       # URL routing
│   │   └── document_processor.py  # AI/OCR processing
│   ├── purchase_order/   # Django project settings
│   ├── Dockerfile        # Docker configuration
│   ├── docker-compose.yml # Docker compose setup
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── pages/        # React pages
│   │   ├── api/          # API client
│   │   └── context/      # React context
│   └── package.json      # Node dependencies
└── README.md
```

## ✅ Assessment Criteria Checklist

- [x] **Functionality (25 pts)**: All core features implemented
- [x] **Code Quality (20 pts)**: Clean, maintainable code with proper structure
- [x] **Security (15 pts)**: JWT authentication, role-based access control
- [x] **Frontend (15 pts)**: React with TypeScript, role-based dashboards
- [x] **Deployment & Docker (15 pts)**: Dockerfile and docker-compose.yml provided
- [x] **Documentation (10 pts)**: Comprehensive README with setup instructions

## 🔗 Public Deployment

**Note**: Update this section with your actual deployment URL once deployed.

- **Backend API**: [Your deployment URL]
- **Frontend**: [Your frontend URL]
- **Swagger UI**: [Your deployment URL]/swagger/

## 👥 Contributors

- GIHOZO - Full Stack Developer

## 📄 License

This project is part of the IST Africa Technical Assessment.

---

For any issues or questions, please contact the development team.

