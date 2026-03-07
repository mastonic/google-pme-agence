import asyncio
import os
import sys

# Need to add google-pme to path to import backend
sys.path.append(os.path.abspath("."))

from backend.main import deploy_business, get_db
from backend.models.database import SessionLocal, Business
import json

db = SessionLocal()

def test_deploy(business_id):
    print(f"Testing deployment for {business_id}")
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        print("Business not found")
        return
    
    # Force status to pending_validation so it passes the check
    b.status = "pending_validation"
    db.commit()

    try:
        res = asyncio.run(deploy_business(business_id, db))
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_deploy("ChIJBaFYPAefaowRvgAZONKYtiU")
