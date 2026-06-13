import razorpay
client = razorpay.Client(auth=("rzp_test_T17x2iLw1nWnq3", "i1mjxYoDbCwKD2IBl8QsEEcn"))
try:
    order = client.order.create({
        "amount": 5000,
        "currency": "INR",
        "receipt": "receipt_70e93f2b-12e9-4d3d-9988-895a7d7dbaaa",
    })
    print(order)
except Exception as e:
    print(f"Error: {e}")
