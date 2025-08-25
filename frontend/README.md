# Smart Health System Frontend

A Streamlit-based frontend for the Smart Health System, providing a bilingual (Hebrew/English) interface for user profile collection and medical Q&A.

## Features

- **Two-Phase Workflow**: Profile collection followed by medical chat
- **Bilingual Support**: Hebrew and English with proper RTL text handling
- **Real-time Backend Integration**: Connects to FastAPI backend
- **Session Management**: Persistent user state across interactions
- **Responsive Design**: Works on desktop and mobile devices
- **Debug Mode**: Developer tools for troubleshooting

## Project Structure

```
frontend/
├── streamlit_app.py              # Main entry point
├── components/
│   ├── __init__.py
│   ├── profile_collector.py     # Phase 1: User info collection
│   ├── chat_interface.py        # Phase 2: Q&A chatbot
│   ├── session_manager.py       # Session state management
│   └── api_client.py            # Backend API communication
├── utils/
│   ├── __init__.py
│   ├── validators.py            # Frontend validation helpers
│   ├── formatters.py            # Text/UI formatting utilities
│   └── hebrew_support.py        # RTL/Hebrew display helpers
├── config/
│   ├── __init__.py
│   └── settings.py              # Configuration and constants
├── assets/
│   └── style.css                # Custom CSS for Hebrew/RTL
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

## Installation

1. **Install Dependencies**:

   ```bash
   cd frontend
   pip install -r requirements.txt
   ```

2. **Set Backend URL** (optional):

   ```bash
   export BACKEND_URL="http://127.0.0.1:8001"
   ```

3. **Run the Application**:
   ```bash
   streamlit run streamlit_app.py
   ```

## Usage

### Phase 1: Profile Collection

1. Select your preferred language (Hebrew/English)
2. Start the registration process
3. Answer the LLM's questions to build your profile
4. Review and confirm your information
5. Proceed to the chat phase

### Phase 2: Medical Q&A

1. Ask medical questions in natural language
2. Receive personalized responses based on your profile
3. View source citations for transparency
4. Access debug information if needed

## Configuration

### Backend Integration

The frontend connects to the backend API at the URL specified in `config/settings.py`:

```python
BACKEND_BASE_URL = "http://127.0.0.1:8001"
```

### Language Settings

Default language is Hebrew. Users can toggle between languages using the language button.

### Debug Mode

Enable debug mode to see:

- API request/response details
- Session state information
- Backend connection status
- Conversation statistics

## API Integration

The frontend communicates with these backend endpoints:

- `POST /collect_user_info` - Profile collection
- `POST /chat` - Medical Q&A
- `GET /health` - Backend health check
- `GET /kb_stats` - Knowledge base statistics

## Hebrew/RTL Support

The application includes comprehensive Hebrew and RTL text support:

- **Text Direction**: Automatic RTL detection and formatting
- **Font Selection**: Optimized Hebrew font stack
- **UI Layout**: RTL-aware component alignment
- **Mixed Content**: Proper handling of Hebrew/English mixed text

## Session Management

The application maintains session state including:

- Current phase (collection/chat)
- User profile data
- Conversation history
- Language preference
- Debug mode status

## Error Handling

The frontend includes robust error handling for:

- Backend connectivity issues
- API request failures
- Validation errors
- Session state corruption

## Development

### Adding New Components

1. Create component file in `components/`
2. Import and use `SessionManager` for state
3. Use `api_client` for backend communication
4. Follow Hebrew/RTL patterns from existing components

### Customizing Styling

Edit `assets/style.css` to modify:

- Color schemes
- Typography
- Layout spacing
- RTL-specific styles

### Environment Variables

- `BACKEND_URL`: Backend API base URL
- `DEBUG_MODE`: Enable debug features (optional)

## Troubleshooting

### Backend Connection Issues

1. Verify backend is running on correct port
2. Check `BACKEND_URL` environment variable
3. Test backend health endpoint directly
4. Review network/firewall settings

### Hebrew Text Display Issues

1. Ensure browser supports Hebrew fonts
2. Check CSS is loading properly
3. Verify text direction detection logic
4. Test with different Hebrew text samples

### Session State Problems

1. Clear browser cache and cookies
2. Use "Reset System" button in footer
3. Check browser developer console for errors
4. Enable debug mode for detailed information

## Browser Support

Tested and supported browsers:

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

The application is optimized for:

- Fast initial load times
- Responsive user interactions
- Efficient API communication
- Minimal memory usage

## Security

Security considerations:

- Input validation on frontend and backend
- Sensitive data masking in logs
- HTTPS support (when configured)
- Session data protection
