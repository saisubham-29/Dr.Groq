# Dr.Groq REST API Documentation

Base URL: `http://your-server:5000/api`

## Authentication
Currently no authentication required. Add API keys in production.

## Endpoints

### 1. Send Chat Message

**POST** `/api/chat`

Send a message and get AI response.

**Request:**
```json
{
  "session_id": "optional-uuid-string",
  "message": "I have a headache for 2 days"
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "response": "I understand this must be concerning...",
  "is_emergency": false,
  "severity": "low",
  "patient_context": {
    "age": "45",
    "conditions": ["diabetes"],
    "medications": ["metformin"]
  },
  "show_booking": false,
  "symptoms": ["headache"]
}
```

**Fields:**
- `session_id` (optional in request): UUID to maintain conversation. If not provided, a new one is created.
- `message` (required): User's message
- `response`: AI's response
- `is_emergency`: `true` if emergency detected
- `severity`: `"low"`, `"medium"`, or `"high"`
- `patient_context`: Extracted patient information
- `show_booking`: `true` if booking UI should be shown
- `symptoms`: List of detected symptoms

**Status Codes:**
- `200`: Success
- `400`: Bad request (missing message)
- `500`: Server error

**Example (cURL):**
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "message": "I have a fever"
  }'
```

**Example (Android - Retrofit):**
```kotlin
interface DrGroqApi {
    @POST("api/chat")
    suspend fun sendMessage(@Body request: ChatRequest): ChatResponse
}

data class ChatRequest(
    val session_id: String? = null,
    val message: String
)

data class ChatResponse(
    val session_id: String,
    val response: String,
    val is_emergency: Boolean,
    val severity: String,
    val patient_context: PatientContext?,
    val show_booking: Boolean,
    val symptoms: List<String>
)
```

---

### 2. Get Chat History

**GET** `/api/chat/{session_id}`

Retrieve conversation history for a session.

**Response:**
```json
{
  "session_id": "uuid-string",
  "conversation_history": [
    {
      "role": "user",
      "content": "I have a headache"
    },
    {
      "role": "assistant",
      "content": "I understand..."
    }
  ],
  "patient_context": {
    "age": "45",
    "conditions": ["diabetes"]
  },
  "symptoms": ["headache"]
}
```

**Status Codes:**
- `200`: Success
- `404`: Session not found
- `500`: Server error

**Example:**
```bash
curl http://localhost:5000/api/chat/test-123
```

---

### 3. Delete Chat Session

**DELETE** `/api/chat/{session_id}`

Clear conversation history and patient context.

**Response:**
```json
{
  "status": "ok"
}
```

**Example:**
```bash
curl -X DELETE http://localhost:5000/api/chat/test-123
```

---

### 4. Get Available Appointment Slots

**GET** `/api/booking/slots?specialty=Cardiologist&days=7`

Get available appointment slots.

**Query Parameters:**
- `specialty` (optional): Specialty name. Default: "General Physician"
- `days` (optional): Number of days ahead. Default: 7

**Response:**
```json
{
  "specialty": "Cardiologist",
  "slots": [
    {
      "date": "2026-02-13",
      "time": "09:00",
      "specialty": "Cardiologist",
      "available": true
    },
    {
      "date": "2026-02-13",
      "time": "10:00",
      "specialty": "Cardiologist",
      "available": true
    }
  ],
  "available_specialties": [
    "General Physician",
    "Cardiologist",
    "Endocrinologist",
    "Neurologist",
    "Dermatologist",
    "Orthopedic",
    "Gastroenterologist",
    "Pulmonologist"
  ]
}
```

**Example:**
```bash
curl "http://localhost:5000/api/booking/slots?specialty=Cardiologist&days=7"
```

---

## Session Management

### How Sessions Work

1. **First Request**: Send message without `session_id`
   - Server creates new session and returns `session_id`
   - Store this `session_id` in your app

2. **Subsequent Requests**: Include `session_id` in all requests
   - Server maintains conversation context
   - Patient information is remembered

3. **Clear Session**: Call DELETE endpoint to reset

### Example Flow

```kotlin
// First message
val response1 = api.sendMessage(ChatRequest(
    message = "I'm 45 years old with diabetes"
))
val sessionId = response1.session_id  // Save this

// Second message (with context)
val response2 = api.sendMessage(ChatRequest(
    session_id = sessionId,
    message = "I have a headache"
))
// Bot remembers age and diabetes

// Clear session
api.deleteSession(sessionId)
```

---

## Error Handling

All errors return JSON:

```json
{
  "error": "Error message here"
}
```

**Common Errors:**
- `400`: Missing required fields
- `404`: Session not found
- `500`: Server error (check logs)

---

## Android Integration Example

### 1. Add Dependencies (build.gradle)

```gradle
dependencies {
    implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'com.squareup.retrofit2:converter-gson:2.9.0'
    implementation 'com.squareup.okhttp3:logging-interceptor:4.11.0'
}
```

### 2. Create API Interface

```kotlin
interface DrGroqApi {
    @POST("api/chat")
    suspend fun sendMessage(@Body request: ChatRequest): ChatResponse
    
    @GET("api/chat/{session_id}")
    suspend fun getHistory(@Path("session_id") sessionId: String): ChatHistory
    
    @DELETE("api/chat/{session_id}")
    suspend fun deleteSession(@Path("session_id") sessionId: String): StatusResponse
    
    @GET("api/booking/slots")
    suspend fun getSlots(
        @Query("specialty") specialty: String = "General Physician",
        @Query("days") days: Int = 7
    ): BookingSlots
}
```

### 3. Create Retrofit Instance

```kotlin
object ApiClient {
    private const val BASE_URL = "http://your-server:5000/"
    
    val api: DrGroqApi by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(DrGroqApi::class.java)
    }
}
```

### 4. Use in ViewModel

```kotlin
class ChatViewModel : ViewModel() {
    private var sessionId: String? = null
    
    fun sendMessage(message: String) {
        viewModelScope.launch {
            try {
                val response = ApiClient.api.sendMessage(
                    ChatRequest(sessionId, message)
                )
                sessionId = response.session_id
                
                if (response.is_emergency) {
                    // Show emergency alert
                }
                
                // Update UI with response
                _messages.value += response
                
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    fun clearSession() {
        viewModelScope.launch {
            sessionId?.let { ApiClient.api.deleteSession(it) }
            sessionId = null
        }
    }
}
```

---

## Testing

### Test with cURL

```bash
# Send message
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I have a fever"}'

# Get history
curl http://localhost:5000/api/chat/SESSION_ID

# Get slots
curl "http://localhost:5000/api/booking/slots?specialty=Cardiologist"

# Delete session
curl -X DELETE http://localhost:5000/api/chat/SESSION_ID
```

### Test with Postman

1. Import collection from `postman_collection.json` (if provided)
2. Set base URL: `http://localhost:5000`
3. Test each endpoint

---

## CORS

CORS is enabled for all origins. In production, restrict to your Android app:

```python
CORS(app, origins=["https://your-app.com"])
```

---

## Rate Limiting

Not implemented. Add in production:

```python
from flask_limiter import Limiter

limiter = Limiter(app, default_limits=["100 per hour"])
```

---

## Deployment

### Local Network (for testing)

```bash
python3 chatbot_app.py
# Access from Android: http://YOUR_LOCAL_IP:5000
```

### Production (Heroku/AWS/etc)

Update `BASE_URL` in Android app to production URL.

---

## Support

For issues, check:
- Server logs
- Network connectivity
- API endpoint URLs
- Request/response format
