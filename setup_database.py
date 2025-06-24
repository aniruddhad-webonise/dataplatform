#!/usr/bin/env python3
"""
Setup script to create a sample SQLite database with test data
for testing the MCP SQL Analytics Server and future ML predictions.
"""

import sqlite3
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

def create_sample_database():
    """Create a sample database with test data suitable for ML predictions."""
    
    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    db_path = data_dir / "analytics.db"
    
    # Remove existing database if it exists
    if db_path.exists():
        os.remove(db_path)
    
    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Creating sample database at: {db_path}")
    
    # Create tables with ML-friendly features
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            signup_date DATE NOT NULL,
            age INTEGER,
            gender TEXT,
            country TEXT,
            subscription_type TEXT DEFAULT 'basic',
            last_login_date DATE,
            total_logins INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            churn_risk_score DECIMAL(3,2) DEFAULT 0.5
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            stock_quantity INTEGER DEFAULT 0,
            created_date DATE NOT NULL,
            rating DECIMAL(3,2) DEFAULT 4.0,
            review_count INTEGER DEFAULT 0,
            is_featured BOOLEAN DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            order_date DATE NOT NULL,
            status TEXT DEFAULT 'completed',
            payment_method TEXT DEFAULT 'credit_card',
            shipping_address TEXT,
            discount_applied DECIMAL(5,2) DEFAULT 0.0,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            revenue DECIMAL(10,2) NOT NULL,
            sale_date DATE NOT NULL,
            region TEXT,
            sales_channel TEXT DEFAULT 'online',
            promotion_code TEXT,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE customer_behavior (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            session_date DATE NOT NULL,
            pages_visited INTEGER DEFAULT 1,
            time_spent_minutes INTEGER DEFAULT 5,
            items_viewed INTEGER DEFAULT 1,
            items_added_to_cart INTEGER DEFAULT 0,
            items_purchased INTEGER DEFAULT 0,
            bounce_rate DECIMAL(3,2) DEFAULT 0.0,
            conversion_rate DECIMAL(3,2) DEFAULT 0.0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE product_reviews (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            review_text TEXT,
            review_date DATE NOT NULL,
            helpful_votes INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE marketing_campaigns (
            id INTEGER PRIMARY KEY,
            campaign_name TEXT NOT NULL,
            campaign_type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            budget DECIMAL(10,2) NOT NULL,
            spent_amount DECIMAL(10,2) DEFAULT 0.0,
            impressions INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            conversions INTEGER DEFAULT 0,
            conversion_rate DECIMAL(5,2) DEFAULT 0.0
        )
    ''')
    
    # Insert sample data
    print("Inserting sample data...")
    
    # Generate more users (50 instead of 10)
    users_data = []
    countries = ['USA', 'Canada', 'UK', 'Australia', 'Germany', 'France', 'Spain', 'Italy', 'Japan', 'Brazil']
    subscription_types = ['basic', 'premium', 'enterprise']
    
    for i in range(1, 51):
        name = f"User {i}"
        email = f"user{i}@example.com"
        signup_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 120))
        age = random.randint(18, 65)
        gender = random.choice(['Male', 'Female'])
        country = random.choice(countries)
        subscription_type = random.choice(subscription_types)
        last_login = signup_date + timedelta(days=random.randint(0, 30))
        total_logins = random.randint(1, 50)
        is_active = random.choice([0, 1]) if total_logins < 5 else 1
        churn_risk = random.uniform(0.1, 0.9)
        
        users_data.append((
            i, name, email, signup_date.strftime('%Y-%m-%d'), age, gender, country,
            subscription_type, last_login.strftime('%Y-%m-%d'), total_logins, is_active, churn_risk
        ))
    
    cursor.executemany('''
        INSERT INTO users (id, name, email, signup_date, age, gender, country, subscription_type, 
                          last_login_date, total_logins, is_active, churn_risk_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', users_data)
    
    # Generate more products (25 instead of 10)
    products_data = []
    categories = ['Electronics', 'Home & Kitchen', 'Sports', 'Fashion', 'Books', 'Toys', 'Health', 'Automotive']
    
    for i in range(1, 26):
        name = f"Product {i}"
        category = random.choice(categories)
        price = round(random.uniform(10.0, 2000.0), 2)
        stock = random.randint(0, 200)
        created_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 90))
        rating = round(random.uniform(3.0, 5.0), 2)
        review_count = random.randint(0, 100)
        is_featured = random.choice([0, 1])
        
        products_data.append((
            i, name, category, price, stock, created_date.strftime('%Y-%m-%d'),
            rating, review_count, is_featured
        ))
    
    cursor.executemany('''
        INSERT INTO products (id, name, category, price, stock_quantity, created_date, 
                             rating, review_count, is_featured)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', products_data)
    
    # Generate more orders (100 instead of 15)
    orders_data = []
    payment_methods = ['credit_card', 'paypal', 'bank_transfer', 'crypto']
    
    for i in range(1, 101):
        user_id = random.randint(1, 50)
        product_id = random.randint(1, 25)
        quantity = random.randint(1, 3)
        amount = round(random.uniform(20.0, 500.0), 2)
        order_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 120))
        status = random.choice(['completed', 'pending', 'cancelled'])
        payment_method = random.choice(payment_methods)
        discount = round(random.uniform(0.0, 50.0), 2) if random.random() > 0.7 else 0.0
        
        orders_data.append((
            i, user_id, product_id, quantity, amount, order_date.strftime('%Y-%m-%d'),
            status, payment_method, f"Address {i}", discount
        ))
    
    cursor.executemany('''
        INSERT INTO orders (id, user_id, product_id, quantity, amount, order_date, status,
                           payment_method, shipping_address, discount_applied)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', orders_data)
    
    # Generate more sales data (150 instead of 15)
    sales_data = []
    regions = ['North America', 'Europe', 'Asia Pacific', 'Latin America', 'Middle East']
    sales_channels = ['online', 'mobile', 'in_store', 'marketplace']
    
    for i in range(1, 151):
        product_id = random.randint(1, 25)
        quantity = random.randint(1, 10)
        revenue = round(random.uniform(50.0, 2000.0), 2)
        sale_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 120))
        region = random.choice(regions)
        sales_channel = random.choice(sales_channels)
        promotion_code = f"PROMO{i}" if random.random() > 0.8 else None
        
        sales_data.append((
            i, product_id, quantity, revenue, sale_date.strftime('%Y-%m-%d'),
            region, sales_channel, promotion_code
        ))
    
    cursor.executemany('''
        INSERT INTO sales (id, product_id, quantity, revenue, sale_date, region,
                          sales_channel, promotion_code)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', sales_data)
    
    # Generate customer behavior data (200 records)
    behavior_data = []
    for i in range(1, 201):
        user_id = random.randint(1, 50)
        session_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 120))
        pages_visited = random.randint(1, 20)
        time_spent = random.randint(1, 120)
        items_viewed = random.randint(1, 10)
        items_added_to_cart = random.randint(0, 5)
        items_purchased = random.randint(0, items_added_to_cart)
        bounce_rate = round(random.uniform(0.0, 1.0), 2)
        conversion_rate = round(items_purchased / max(items_viewed, 1), 2)
        
        behavior_data.append((
            i, user_id, session_date.strftime('%Y-%m-%d'), pages_visited, time_spent,
            items_viewed, items_added_to_cart, items_purchased, bounce_rate, conversion_rate
        ))
    
    cursor.executemany('''
        INSERT INTO customer_behavior (id, user_id, session_date, pages_visited, time_spent_minutes,
                                      items_viewed, items_added_to_cart, items_purchased, 
                                      bounce_rate, conversion_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', behavior_data)
    
    # Generate product reviews (100 records)
    reviews_data = []
    for i in range(1, 101):
        user_id = random.randint(1, 50)
        product_id = random.randint(1, 25)
        rating = random.randint(1, 5)
        review_text = f"Review text for product {product_id} by user {user_id}"
        review_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 120))
        helpful_votes = random.randint(0, 20)
        
        reviews_data.append((
            i, user_id, product_id, rating, review_text, review_date.strftime('%Y-%m-%d'), helpful_votes
        ))
    
    cursor.executemany('''
        INSERT INTO product_reviews (id, user_id, product_id, rating, review_text, review_date, helpful_votes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', reviews_data)
    
    # Generate marketing campaigns (20 records)
    campaigns_data = []
    campaign_types = ['email', 'social_media', 'search', 'display', 'video']
    
    for i in range(1, 21):
        campaign_name = f"Campaign {i}"
        campaign_type = random.choice(campaign_types)
        start_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 60))
        end_date = start_date + timedelta(days=random.randint(7, 30))
        budget = round(random.uniform(1000.0, 50000.0), 2)
        spent_amount = round(budget * random.uniform(0.3, 1.0), 2)
        impressions = random.randint(1000, 100000)
        clicks = random.randint(100, 10000)
        conversions = random.randint(10, 1000)
        conversion_rate = round(conversions / max(clicks, 1), 4)
        
        campaigns_data.append((
            i, campaign_name, campaign_type, start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'), budget, spent_amount, impressions,
            clicks, conversions, conversion_rate
        ))
    
    cursor.executemany('''
        INSERT INTO marketing_campaigns (id, campaign_name, campaign_type, start_date, end_date,
                                        budget, spent_amount, impressions, clicks, conversions, conversion_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', campaigns_data)
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print("✅ Enhanced sample database created successfully!")
    print(f"📊 Tables created: users, products, orders, sales, customer_behavior, product_reviews, marketing_campaigns")
    print(f"📈 Sample data inserted:")
    print(f"   - {len(users_data)} users (with churn risk scores)")
    print(f"   - {len(products_data)} products (with ratings)")
    print(f"   - {len(orders_data)} orders (with payment methods)")
    print(f"   - {len(sales_data)} sales (with channels)")
    print(f"   - {len(behavior_data)} customer behavior sessions")
    print(f"   - {len(reviews_data)} product reviews")
    print(f"   - {len(campaigns_data)} marketing campaigns")
    
    # Print sample queries for testing
    print("\n🧪 Sample queries you can test:")
    print("1. SELECT * FROM users LIMIT 5")
    print("2. SELECT COUNT(*) as total_users FROM users WHERE is_active = 1")
    print("3. SELECT category, AVG(price) as avg_price, COUNT(*) as product_count FROM products GROUP BY category")
    print("4. SELECT u.name, SUM(o.amount) as total_spent, u.churn_risk_score FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name ORDER BY total_spent DESC LIMIT 10")
    print("5. SELECT p.name, AVG(pr.rating) as avg_rating, COUNT(pr.id) as review_count FROM products p LEFT JOIN product_reviews pr ON p.id = pr.product_id GROUP BY p.id, p.name HAVING review_count > 0 ORDER BY avg_rating DESC")
    print("6. SELECT region, SUM(revenue) as total_revenue, COUNT(*) as sales_count FROM sales GROUP BY region ORDER BY total_revenue DESC")
    print("7. SELECT campaign_type, AVG(conversion_rate) as avg_conversion, SUM(spent_amount) as total_spent FROM marketing_campaigns GROUP BY campaign_type")
    print("8. SELECT u.age_group, AVG(cb.conversion_rate) as avg_conversion FROM (SELECT id, CASE WHEN age < 30 THEN '18-29' WHEN age < 40 THEN '30-39' WHEN age < 50 THEN '40-49' ELSE '50+' END as age_group FROM users) u JOIN customer_behavior cb ON u.id = cb.user_id GROUP BY u.age_group")
    
    print("\n🤖 ML-Ready Features:")
    print("- Churn prediction: users.churn_risk_score, customer_behavior data")
    print("- Sales forecasting: time-series sales data with regions/channels")
    print("- Customer segmentation: behavior patterns, demographics")
    print("- Product recommendation: purchase history, ratings, reviews")
    print("- Marketing optimization: campaign performance metrics")
    
    return db_path

if __name__ == "__main__":
    create_sample_database() 