# Future Enhancements

This document outlines potential future enhancements for the Job Tracker project.

## Current Enhancements

The following enhancements have recently been implemented:

### 1. Dark Mode Toggle

A user-selectable dark mode has been added to provide better viewing options, especially in low-light environments.

- **Implementation**: CSS-based theme switching with session state persistence
- **Benefits**: Reduced eye strain, better night-time viewing, modern UI appearance
- **Files Modified**: `dashboard.py`

### 2. Mobile Responsiveness

The dashboard has been optimized for mobile device viewing.

- **Implementation**: Responsive layouts, size detection, and optimized controls
- **Benefits**: Better access on smartphones and tablets, improved user experience across devices
- **Files Modified**: `dashboard.py` with viewport detection and responsive CSS

### 3. Pagination Controls

Job listing pagination has been added to improve navigation through large result sets.

- **Implementation**: Pagination controls with session state for maintaining page position
- **Benefits**: Faster page loading, easier navigation through large datasets
- **Files Modified**: `dashboard.py`, `app/api/endpoints/jobs.py`

### 4. Database Indexing

Database indexing has been implemented to optimize query performance.

- **Implementation**: Strategic indexes on frequently queried columns
- **Benefits**: Faster filtering and search operations, reduced database load
- **Files Modified**: `app/db/models.py`

### 5. API Pagination

The API now includes proper pagination with navigation links.

- **Implementation**: Page-based result limiting with metadata and navigation links
- **Benefits**: Improved API performance, better client-side integration
- **Files Modified**: `app/api/endpoints/jobs.py`

### 6. Rate Limiting

Nginx rate limiting has been implemented to protect against API abuse.

- **Implementation**: Request rate limiting per IP address
- **Benefits**: Prevention of API abuse, improved stability
- **Files Modified**: `scripts/job-tracker-nginx.conf`

### 7. Custom Error Pages

Custom error pages have been added for a better user experience.

- **Implementation**: Custom HTML pages for common error codes
- **Benefits**: More user-friendly error messages, brand consistency
- **Files Modified**: Added `scripts/error_pages` directory with HTML templates

### 8. Caching Strategy

A basic caching implementation has been added to improve performance.

- **Implementation**: In-memory caching for API responses
- **Benefits**: Reduced database load, faster response times
- **Files Modified**: Added `app/api/cache.py`

## Potential Future Enhancements

These are potential enhancements that could be implemented in the future:

### 1. User Authentication

Adding user authentication would enable personalized experiences and secure access to the system.

### Implementation Options

#### Option 1: FastAPI's Security Features

```python
# app/auth/models.py
from sqlalchemy import Column, String, Integer, Boolean
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
```

```python
# app/auth/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.auth import crud, schemas

router = APIRouter()

@router.post("/register", response_model=schemas.UserRead)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = crud.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
```

#### Option 2: Auth0 Integration

```python
# app/auth/auth0.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import requests

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
AUTH0_DOMAIN = "your-domain.auth0.com"
API_AUDIENCE = "https://your-api-identifier"
ALGORITHMS = ["RS256"]

def get_public_key():
    url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    response = requests.get(url)
    jwks = response.json()
    return jwks

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            get_public_key(), 
            algorithms=ALGORITHMS,
            audience=API_AUDIENCE
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception
```

### 2. Personal Job Lists

Allow users to save jobs they're interested in and track their application status.

```python
# app/db/models.py
class SavedJob(Base):
    __tablename__ = "saved_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    saved_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Saved")  # Saved, Applied, Interviewing, Rejected, Offered
    notes = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="saved_jobs")
    job = relationship("Job", back_populates="saved_by")
```

### 3. Email Notifications

Send users notifications about new jobs matching their criteria.

```python
# app/notifications/email.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD

def send_job_notification(user_email, jobs):
    message = MIMEMultipart()
    message["From"] = EMAIL_USER
    message["To"] = user_email
    message["Subject"] = f"New Job Matches Found - Job Tracker"
    
    # Create the HTML content
    html = "<html><body>"
    html += "<h2>New Job Matches Found</h2>"
    html += "<p>We found these new jobs matching your criteria:</p>"
    html += "<ul>"
    
    for job in jobs:
        html += f"<li><b>{job.job_title}</b> at {job.company} - <a href='{job.job_url}'>Apply</a></li>"
    
    html += "</ul>"
    html += "<p>Good luck with your job search!</p>"
    html += "</body></html>"
    
    message.attach(MIMEText(html, "html"))
    
    # Connect to the SMTP server and send the email
    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(message)
```

### 4. Enhanced Analytics Dashboard

Add more sophisticated visualizations and analytics.

```python
# dashboard_analytics.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def job_trends_chart(df):
    # Group by date and get counts
    df_trend = df.groupby('date_posted').size().reset_index(name='count')
    df_trend['day_of_week'] = df_trend['date_posted'].dt.day_name()
    
    # Create trend line with moving average
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_trend['date_posted'], 
        y=df_trend['count'],
        mode='markers',
        name='Daily Count'
    ))
    
    # Add 7-day moving average
    df_trend['moving_avg'] = df_trend['count'].rolling(window=7).mean()
    fig.add_trace(go.Scatter(
        x=df_trend['date_posted'], 
        y=df_trend['moving_avg'],
        mode='lines',
        name='7-day Average',
        line=dict(color='red', width=2)
    ))
    
    fig.update_layout(
        title='Job Posting Trends',
        xaxis_title='Date',
        yaxis_title='Number of Jobs',
        height=500
    )
    
    return fig

def location_map(df):
    # Create a choropleth map of job locations
    location_counts = df['location'].value_counts().reset_index()
    location_counts.columns = ['location', 'count']
    
    fig = px.choropleth(
        location_counts,
        locations='location',
        color='count',
        hover_name='location',
        title='Job Distribution by Location',
        color_continuous_scale=px.colors.sequential.Plasma
    )
    
    return fig
```

### 5. AI-Powered Job Matching

Implement machine learning for better job recommendations.

```python
# app/ml/job_matcher.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np

class JobMatcher:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.job_vectors = None
        self.jobs = None
    
    def fit(self, jobs_df):
        """Process job descriptions and generate vectors"""
        # Combine relevant fields for matching
        job_texts = jobs_df.apply(
            lambda x: f"{x['job_title']} {x['description']} {' '.join(x['roles'])}", 
            axis=1
        )
        
        # Create TF-IDF vectors
        self.job_vectors = self.vectorizer.fit_transform(job_texts)
        self.jobs = jobs_df
    
    def get_recommendations(self, profile_text, top_n=10):
        """Find matching jobs based on user profile"""
        # Vectorize the profile text
        profile_vector = self.vectorizer.transform([profile_text])
        
        # Calculate similarity scores
        similarity_scores = cosine_similarity(profile_vector, self.job_vectors)
        
        # Get indices of top matches
        top_indices = np.argsort(similarity_scores[0])[-top_n:][::-1]
        
        # Return the matching jobs
        return self.jobs.iloc[top_indices]
```

### 6. Redis Cache Implementation

Replace the in-memory cache with Redis for more robust caching.

```python
# app/cache.py
import redis
import json
from datetime import timedelta
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache(ttl_seconds=300):
    """
    Decorator that caches the result of a function in Redis
    
    Args:
        ttl_seconds: Time to live in seconds for cache entries
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create a cache key based on function name and arguments
            key_parts = [func.__name__]
            for arg in args:
                key_parts.append(str(arg))
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}:{v}")
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = redis_client.get(cache_key)
            if cached_value:
                return json.loads(cached_value)
            
            # If not in cache, call the function
            result = await func(*args, **kwargs)
            
            # Store result in cache
            redis_client.setex(
                cache_key,
                timedelta(seconds=ttl_seconds),
                json.dumps(result)
            )
            
            return result
        return wrapper
    return decorator
```

### 7. Improved Mobile APP Interface

Create a dedicated mobile UI for better mobile experience:

```python
# mobile_dashboard.py
import streamlit as st

def mobile_layout():
    st.set_page_config(
        page_title="Job Tracker Mobile",
        page_icon="📱",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Top navigation bar
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; background-color: #f0f2f6; position: fixed; top: 0; width: 100%; z-index: 999;">
        <span>📱 Job Tracker</span>
        <div>
            <span onclick="document.querySelector('.sidebar').classList.toggle('show');">☰</span>
        </div>
    </div>
    <style>
        .sidebar { display: none; }
        .sidebar.show { display: block; }
        body { padding-top: 50px; }
    </style>
    """, unsafe_allow_html=True)
    
    # Mobile-optimized job cards
    st.markdown("""
    <style>
    .job-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .job-title {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .job-company {
        font-size: 16px;
        color: #555;
        margin-bottom: 5px;
    }
    .job-details {
        font-size: 14px;
        color: #777;
        display: flex;
        justify-content: space-between;
    }
    .job-cta {
        text-align: center;
        margin-top: 10px;
    }
    .job-cta a {
        display: inline-block;
        background-color: #0066cc;
        color: white;
        padding: 8px 16px;
        border-radius: 5px;
        text-decoration: none;
    }
    </style>
    """, unsafe_allow_html=True)
```

These enhancements can be implemented gradually as user needs evolve and the system grows. The recently added features provide a solid foundation for future improvement.
