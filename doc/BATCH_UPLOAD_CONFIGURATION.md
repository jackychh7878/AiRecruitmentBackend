# Batch Upload Configuration Guide

This guide explains how to configure file upload limits for the batch resume parsing feature.

## Default Limits

The system has the following default limits:

- **Individual file size**: 16MB per PDF file
- **Total batch size**: 200MB for all files combined
- **Maximum files per batch**: 50 files

## Environment Variables

Configure these limits using environment variables:

```bash
# Individual file size limit (in bytes)
# Default: 16MB = 16,777,216 bytes
MAX_CONTENT_LENGTH=16777216

# Total batch upload size limit (in bytes)  
# Default: 200MB = 209,715,200 bytes
# NOTE: Flask will automatically use the larger of the two limits
BATCH_UPLOAD_LIMIT=209715200
```

## Important Configuration Notes

1. **Flask Automatic Configuration**: Flask automatically sets its internal limit to the maximum of `MAX_CONTENT_LENGTH` and `BATCH_UPLOAD_LIMIT`
2. **Separate Validation**: The application validates individual files against `MAX_CONTENT_LENGTH` and total batch size against `BATCH_UPLOAD_LIMIT`
3. **Restart Required**: Changes require restarting the Flask application

## Common File Size Conversions

| Size | Bytes |
|------|-------|
| 1MB | 1,048,576 |
| 5MB | 5,242,880 |
| 10MB | 10,485,760 |
| 16MB | 16,777,216 |
| 25MB | 26,214,400 |
| 50MB | 52,428,800 |
| 100MB | 104,857,600 |
| 200MB | 209,715,200 |
| 500MB | 524,288,000 |

## Troubleshooting Upload Errors

### Error: "413 Request Entity Too Large"

This error occurs when files exceed the configured limits.

**Solutions:**

1. **Reduce file sizes**: Compress PDF files or split large documents
2. **Increase limits**: Update environment variables
3. **Batch smaller sets**: Upload fewer files per batch

### Example: Increasing Limits

To allow 25MB individual files and 500MB total batch:

```bash
# .env file
MAX_CONTENT_LENGTH=26214400      # 25MB
BATCH_UPLOAD_LIMIT=524288000     # 500MB
```

### Example: Production Configuration

For high-volume production environments:

```bash
# Production .env
MAX_CONTENT_LENGTH=52428800      # 50MB per file
BATCH_UPLOAD_LIMIT=1073741824    # 1GB total batch
AI_BULK_MAX_CONCURRENT_WORKERS=10 # More workers
AI_BULK_RATE_LIMIT_DELAY_SECONDS=0.5 # Faster processing
```

## Error Messages

The system provides specific error messages for different limit violations:

- **Individual file too large**: `File {filename} is too large ({size}MB). Maximum individual file size: {limit}MB`
- **Batch too large**: `Total batch size ({size}MB) exceeds limit. Maximum batch size: {limit}MB`
- **General upload error**: `File upload size exceeds limit. Maximum allowed: {limit}MB total`

## Best Practices

1. **Monitor file sizes**: Check PDF file sizes before uploading
2. **Use compression**: Optimize PDFs to reduce file sizes
3. **Progressive uploads**: Start with smaller batches to test limits
4. **Monitor server resources**: Larger limits require more memory and storage
5. **Configure based on usage**: Adjust limits based on typical resume sizes in your organization

## Server Configuration

Remember to also configure your web server (nginx, Apache) and WSGI server (Gunicorn) limits:

### Nginx Configuration
```nginx
client_max_body_size 200M;
```

### Gunicorn Configuration
```bash
# Increase timeout for large uploads
gunicorn --timeout 300 --workers 4 app:app
```

## Restart Required

After changing environment variables, restart the Flask application to apply new limits. 