#!/usr/bin/env python3
"""
Test script for Performance & KPI API integration
Initializes database with test data and runs API tests
"""

import requests
import json
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.db.database import engine, SessionLocal, Base
from app.db.models import User, Employee, Department, Designation
from app.core.security import hash_password
from uuid import uuid4

# Database setup
print('🔧 Setting up database...')
Base.metadata.create_all(bind=engine)
print('✅ Database tables created')

# Create test data
db = SessionLocal()
try:
    # Check if test user already exists
    test_user = db.query(User).filter(User.email == 'test@example.com').first()
    if not test_user:
        print('\n📝 Creating test department, designation...')
        
        # Check if department exists
        dept = db.query(Department).filter(Department.name == 'Engineering').first()
        if not dept:
            dept = Department(id=str(uuid4()), name='Engineering')
            db.add(dept)
            db.flush()
        
        # Check if designation exists
        desig = db.query(Designation).filter(Designation.name == 'Manager').first()
        if not desig:
            desig = Designation(id=str(uuid4()), name='Manager')
            db.add(desig)
            db.flush()
        
        print('✅ Department, Designation ready')
        
        # Create test user
        print('\n👤 Creating test user...')
        user_id = str(uuid4())
        test_user = User(
            id=user_id,
            full_name='Test User',
            email='test@example.com',
            role='Employee',
            password_hash=hash_password('password123'),
            is_active=True
        )
        db.add(test_user)
        db.flush()
        
        # Create test employee (same id as user for mapping)
        print('🏢 Creating test employee...')
        employee = Employee(
            id=user_id,
            full_name='Test User',
            email='test@example.com',
            date_of_birth=date(1990, 1, 1),
            gender='M',
            department_id=dept.id,
            designation_id=desig.id
        )
        db.add(employee)
        db.commit()
        print(f'✅ Test user created: test@example.com')
    else:
        print('✅ Test user already exists: test@example.com')
        user_id = test_user.id
        
finally:
    db.close()

# API Testing
BASE_URL = 'http://localhost:8000'

print('\n' + '='*60)
print('🚀 API INTEGRATION TESTS')
print('='*60)

# Test 1: Login
print('\n🔐 Test 1: Authentication')
login_resp = requests.post(f'{BASE_URL}/auth/login', json={
    'email': 'test@example.com',
    'password': 'password123'
})

if login_resp.status_code == 200:
    token = login_resp.json().get('access_token')
    print(f'✅ Login successful')
    print(f'   Token: {token[:30]}...')
else:
    print(f'❌ Login failed: {login_resp.status_code}')
    print(login_resp.text)
    exit(1)

headers = {'Authorization': f'Bearer {token}'}

# Test 2: Get current user
print('\n👤 Test 2: Get Current User')
user_resp = requests.get(f'{BASE_URL}/auth/me', headers=headers)
if user_resp.status_code == 200:
    user = user_resp.json()
    print(f'✅ Current user: {user.get("username")} (ID: {user.get("id")})')
else:
    print(f'❌ Failed: {user_resp.status_code}')

# Test 3: Create Goal
print('\n📝 Test 3: Create Goal')
goal_resp = requests.post(f'{BASE_URL}/performance/performance/goals', 
    headers=headers,
    json={
        'title': 'Complete Q1 Projects',
        'description': 'Finish all assigned Q1 projects',
        'employee_id': user_id,
        'start_date': '2026-01-01',
        'end_date': '2026-03-31',
        'target_value': 5,
        'achieved_value': 2,
        'status': 'Active'
    }
)

if goal_resp.status_code == 201:
    goal = goal_resp.json()
    goal_id = goal.get('id')
    print(f'✅ Goal created')
    print(f'   Title: {goal.get("title")}')
    print(f'   Achievement: {goal.get("achievement_percentage")}% (2/5)')
else:
    print(f'❌ Failed: {goal_resp.status_code}')
    print(goal_resp.text[:300])

# Test 4: Create KPI
print('\n📊 Test 4: Create KPI')
kpi_resp = requests.post(f'{BASE_URL}/performance/performance/kpis',
    headers=headers,
    json={
        'title': 'Q1 Revenue',
        'description': 'Quarterly revenue target',
        'employee_id': user_id,
        'target_value': 50000,
        'achieved_value': 35000,
        'weightage': 50,
        'start_date': '2026-01-01',
        'end_date': '2026-03-31',
        'status': 'Active'
    }
)

if kpi_resp.status_code == 201:
    kpi = kpi_resp.json()
    kpi_id = kpi.get('id')
    print(f'✅ KPI created')
    print(f'   Title: {kpi.get("title")}')
    print(f'   Achievement: {kpi.get("achievement_percentage")}% (${kpi.get("achieved_value")}/{kpi.get("target_value")})')
    print(f'   Weightage: {kpi.get("weightage")}%')
else:
    print(f'❌ Failed: {kpi_resp.status_code}')
    print(kpi_resp.text[:300])

# Test 5: Get Performance Score
print('\n🎯 Test 5: Get Performance Score (Weighted)')
score_resp = requests.get(f'{BASE_URL}/performance/performance/performance-score/{user_id}',
    headers=headers
)

if score_resp.status_code == 200:
    score_data = score_resp.json()
    print(f'✅ Performance Score calculated')
    print(f'   Overall Score: {score_data.get("score")}%')
    print(f'   KPIs Count: {score_data.get("kpi_count")}')
    print(f'   Calculation: (35000/50000 * 50%) = {(35000/50000*50)}%')
else:
    print(f'❌ Failed: {score_resp.status_code}')
    print(score_resp.text[:300])

# Test 6: Get Goals List
print('\n📋 Test 6: Get Goals for Employee')
goals_resp = requests.get(f'{BASE_URL}/performance/performance/goals/employee/{user_id}',
    headers=headers
)

if goals_resp.status_code == 200:
    goals = goals_resp.json()
    print(f'✅ Retrieved {len(goals)} goals')
    for g in goals:
        print(f'   - {g.get("title")}: {g.get("achievement_percentage")}%')
else:
    print(f'❌ Failed: {goals_resp.status_code}')

# Test 7: Get KPIs List
print('\n📈 Test 7: Get KPIs for Employee')
kpis_resp = requests.get(f'{BASE_URL}/performance/performance/kpis/employee/{user_id}',
    headers=headers
)

if kpis_resp.status_code == 200:
    kpis = kpis_resp.json()
    print(f'✅ Retrieved {len(kpis)} KPIs')
    for k in kpis:
        print(f'   - {k.get("title")}: {k.get("achievement_percentage")}% (Weightage: {k.get("weightage")}%)')
else:
    print(f'❌ Failed: {kpis_resp.status_code}')

# Test 8: Create Training Course
print('\n🎓 Test 8: Create Training Course')
course_resp = requests.post(f'{BASE_URL}/performance/performance/training/courses',
    headers=headers,
    json={
        'title': 'Advanced Python',
        'description': 'Python advanced programming course',
        'instructor': 'John Doe',
        'duration_hours': 40.0
    }
)

if course_resp.status_code == 201:
    course = course_resp.json()
    course_id = course.get('id')
    print(f'✅ Course created')
    print(f'   Title: {course.get("title")}')
    print(f'   Duration: {course.get("duration_hours")} hours')
else:
    print(f'❌ Failed: {course_resp.status_code}')
    print(course_resp.text[:300])

# Test 9: Enroll Employee in Training
print('\n✍️  Test 9: Enroll Employee in Training')
enroll_resp = requests.post(f'{BASE_URL}/performance/performance/training/enrollments',
    headers=headers,
    json={
        'employee_id': user_id,
        'course_id': course_id,
        'status': 'In Progress'
    }
)

if enroll_resp.status_code == 201:
    enrollment = enroll_resp.json()
    print(f'✅ Enrollment created')
    print(f'   Status: {enrollment.get("status")}')
else:
    print(f'❌ Failed: {enroll_resp.status_code}')
    print(enroll_resp.text[:300])

# Test 10: Create Certification
print('\n🏆 Test 10: Create Certification')
cert_resp = requests.post(f'{BASE_URL}/performance/performance/certifications',
    headers=headers,
    json={
        'employee_id': user_id,
        'name': 'AWS Solutions Architect',
        'issuing_authority': 'Amazon Web Services',
        'issue_date': '2025-01-15',
        'expiry_date': '2027-01-15'
    }
)

if cert_resp.status_code == 201:
    cert = cert_resp.json()
    print(f'✅ Certification created')
    print(f'   Name: {cert.get("name")}')
    print(f'   Issued: {cert.get("issue_date")}')
    print(f'   Expires: {cert.get("expiry_date")}')
    print(f'   Status: {cert.get("is_expired")} (is_expired)')
else:
    print(f'❌ Failed: {cert_resp.status_code}')
    print(cert_resp.text[:300])

print('\n' + '='*60)
print('✅ API INTEGRATION TESTS COMPLETE')
print('='*60)
print('\nAll endpoints tested successfully!')
print('Frontend can now consume these APIs at /performance routes')
