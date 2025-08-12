#!/usr/bin/env python3
"""
Test script for Bulk AI Regeneration APIs
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:5000/api"

def test_get_stats():
    """Test getting bulk regeneration statistics"""
    print("🔍 Testing GET /ai-summary/bulk-regenerate/stats")
    
    try:
        response = requests.get(f"{API_BASE_URL}/candidates/ai-summary/bulk-regenerate/stats")
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get('profile_statistics', {})
            capacity = data.get('processing_capacity', {})
            recommendations = data.get('recommendations', [])
            
            print(f"✅ Statistics retrieved:")
            print(f"   📊 Total profiles: {stats.get('total_profiles', 0)}")
            print(f"   📊 Active profiles: {stats.get('active_profiles', 0)}")
            print(f"   📊 With AI summary: {stats.get('profiles_with_ai_summary', 0)}")
            print(f"   ⚙️  Max workers: {capacity.get('max_concurrent_workers', 0)}")
            print(f"   ⏱️  Estimated time: {capacity.get('estimated_total_processing_hours', 0)} hours")
            
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   - {rec}")
            
            return data
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_start_bulk_regeneration(prompt_template_id=None):
    """Test starting bulk regeneration"""
    print(f"\n🔍 Testing POST /ai-summary/bulk-regenerate")
    
    payload = {
        "created_by": "test_user"
    }
    
    if prompt_template_id:
        payload["prompt_template_id"] = prompt_template_id
        print(f"   Using template ID: {prompt_template_id}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/candidates/ai-summary/bulk-regenerate",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                job_id = data.get('job_id')
                print(f"✅ Bulk regeneration started!")
                print(f"   🆔 Job ID: {job_id}")
                print(f"   📝 Message: {data.get('message')}")
                
                warning = data.get('warning')
                if warning:
                    print(f"   ⚠️  Warning: {warning}")
                
                return job_id
            else:
                print(f"⚠️ Job not started: {data.get('message')}")
                return None
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_get_job_status(job_id):
    """Test getting job status"""
    print(f"\n🔍 Testing GET /ai-summary/bulk-regenerate/jobs/{job_id}")
    
    try:
        response = requests.get(f"{API_BASE_URL}/candidates/ai-summary/bulk-regenerate/jobs/{job_id}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Job status retrieved:")
            print(f"   🆔 Job ID: {data.get('job_id')}")
            print(f"   📊 Status: {data.get('status')}")
            print(f"   👤 Created by: {data.get('created_by')}")
            print(f"   🕐 Started: {data.get('started_at')}")
            
            total = data.get('total_profiles', 0)
            processed = data.get('processed_profiles', 0)
            successful = data.get('successful_updates', 0)
            failed = data.get('failed_updates', 0)
            
            if total > 0:
                progress_pct = (processed / total) * 100
                print(f"   📈 Progress: {processed}/{total} ({progress_pct:.1f}%)")
                print(f"   ✅ Successful: {successful}")
                print(f"   ❌ Failed: {failed}")
                
                current_profile = data.get('current_profile_id')
                if current_profile:
                    print(f"   🔄 Current profile: {current_profile}")
                
                estimated = data.get('estimated_completion')
                if estimated:
                    print(f"   ⏰ Estimated completion: {estimated}")
            
            errors = data.get('errors', [])
            if errors:
                print(f"   🚨 Errors ({len(errors)}):")
                for error in errors[-3:]:  # Show last 3 errors
                    print(f"      - {error}")
                if len(errors) > 3:
                    print(f"      ... and {len(errors) - 3} more errors")
            
            return data
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_list_all_jobs():
    """Test listing all jobs"""
    print(f"\n🔍 Testing GET /ai-summary/bulk-regenerate/jobs")
    
    try:
        response = requests.get(f"{API_BASE_URL}/candidates/ai-summary/bulk-regenerate/jobs")
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('jobs', [])
            total_jobs = data.get('total_jobs', 0)
            
            print(f"✅ Found {total_jobs} jobs:")
            
            for job in jobs:
                job_id = job.get('job_id', 'unknown')
                status = job.get('status', 'unknown')
                started = job.get('started_at', 'unknown')
                created_by = job.get('created_by', 'unknown')
                
                total = job.get('total_profiles', 0)
                processed = job.get('processed_profiles', 0)
                
                print(f"   📋 {job_id}")
                print(f"      Status: {status} | By: {created_by} | Started: {started}")
                if total > 0:
                    progress_pct = (processed / total) * 100
                    print(f"      Progress: {processed}/{total} ({progress_pct:.1f}%)")
                print()
            
            return data
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_cancel_job(job_id):
    """Test cancelling a job"""
    print(f"\n🔍 Testing DELETE /ai-summary/bulk-regenerate/jobs/{job_id}")
    
    try:
        response = requests.delete(f"{API_BASE_URL}/candidates/ai-summary/bulk-regenerate/jobs/{job_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cancel request sent:")
            print(f"   📝 Success: {data.get('success')}")
            print(f"   📝 Message: {data.get('message')}")
            return True
        else:
            data = response.json()
            print(f"⚠️ Cancel failed:")
            print(f"   📝 Success: {data.get('success')}")
            print(f"   📝 Message: {data.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def monitor_job_progress(job_id, max_duration_minutes=5):
    """Monitor job progress for a specified duration"""
    print(f"\n👀 Monitoring job {job_id} for up to {max_duration_minutes} minutes...")
    
    start_time = time.time()
    max_duration_seconds = max_duration_minutes * 60
    check_interval = 10  # Check every 10 seconds
    
    while time.time() - start_time < max_duration_seconds:
        status_data = test_get_job_status(job_id)
        
        if status_data:
            status = status_data.get('status')
            
            if status in ['completed', 'failed', 'cancelled']:
                print(f"\n🏁 Job finished with status: {status}")
                break
        
        print(f"   ⏳ Waiting {check_interval} seconds before next check...")
        time.sleep(check_interval)
    else:
        print(f"\n⏰ Monitoring timeout reached ({max_duration_minutes} minutes)")

if __name__ == "__main__":
    print("🧪 Bulk AI Regeneration API Test")
    print("=" * 50)
    
    # Step 1: Get current statistics
    stats = test_get_stats()
    
    if not stats:
        print("\n❌ Cannot proceed without statistics")
        exit(1)
    
    profile_stats = stats.get('profile_statistics', {})
    active_profiles = profile_stats.get('active_profiles', 0)
    
    if active_profiles == 0:
        print("\n⚠️ No active profiles found. Cannot test bulk regeneration.")
        exit(0)
    
    print(f"\n📊 Ready to test with {active_profiles} active profiles")
    
    # Step 2: List current jobs
    test_list_all_jobs()
    
    # Step 3: Ask user confirmation for starting a job
    print("\n" + "=" * 50)
    print("⚠️  CAUTION: About to start bulk regeneration job")
    print("This will:")
    print("- Process ALL active candidate profiles")
    print("- Regenerate AI summaries and embeddings")
    print("- Consume Azure OpenAI credits")
    print("- Take significant time to complete")
    
    # For safety, we'll just test starting the job but cancel it quickly
    user_input = input("\n❓ Start test job? (y/N): ").strip().lower()
    
    if user_input == 'y':
        # Step 4: Start bulk regeneration
        job_id = test_start_bulk_regeneration()
        
        if job_id:
            # Step 5: Monitor progress briefly
            monitor_job_progress(job_id, max_duration_minutes=1)
            
            # Step 6: Cancel the job for safety
            print("\n🛑 Cancelling test job for safety...")
            test_cancel_job(job_id)
            
            # Step 7: Check final status
            time.sleep(2)
            test_get_job_status(job_id)
        
        # Step 8: List all jobs again
        test_list_all_jobs()
    
    else:
        print("✅ Test skipped - no job started")
    
    print("\n💡 Available endpoints:")
    print("   GET    /api/candidates/ai-summary/bulk-regenerate/stats")
    print("   POST   /api/candidates/ai-summary/bulk-regenerate")
    print("   GET    /api/candidates/ai-summary/bulk-regenerate/jobs")
    print("   GET    /api/candidates/ai-summary/bulk-regenerate/jobs/{job_id}")
    print("   DELETE /api/candidates/ai-summary/bulk-regenerate/jobs/{job_id}")
    
    print("\n🔧 Environment variables:")
    print("   AI_BULK_MAX_CONCURRENT_WORKERS=5  # Max parallel workers")
    print("   AI_BULK_RATE_LIMIT_DELAY_SECONDS=1.0  # Delay between processes") 