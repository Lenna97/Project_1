from flask import Flask, jsonify,json, request, render_template
import sqlite3,logging
from typing import List, Tuple, Any
from pymongo import MongoClient

app = Flask(__name__)
DATABASE = 'users_vouchers.db'
MONGODB_URI = 'mongodb://localhost:27017/'
MONGODB_DB = 'user_spendings'


# def insert_to_mongodb(user_id: int, money_spent: float):
#     client = MongoClient(MONGODB_URI)
#     db = client[MONGODB_DB]

#     user_spending = {"user_id": user_id, "money_spent": money_spent}
#     result = db.user_spendings.insert_one(user_spending)
#     return result.inserted_id
    
def query_db(query: str, args: Tuple = ()) -> List[Tuple[Any, ...]]:
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute(query, args)
    data = cur.fetchall()
    conn.close()
    return data

@app.route('/')
def serve_index_html():
    return render_template('index.html')

@app.route('/total_spending', methods=['GET'])
def get_total_spending():
    try:
        user_id = request.args.get('user_id')
        if user_id is None:
            return jsonify({'error': 'Missing user_id parameter'}), 400

        user_id = int(user_id)

        query = 'SELECT ui.user_id, ui.name, ui.age, SUM(us.money_spent) as total_spending ' \
                'FROM user_info ui ' \
                'INNER JOIN user_spending us ON ui.user_id = us.user_id ' \
                'WHERE ui.user_id = ? ' \
                'GROUP BY ui.user_id, ui.name, ui.age'

        result = query_db(query, (user_id,))

        if not result:
            return jsonify({'error': 'User not found'}), 404

        else:
            user_data = {
                'user_id': result[0][0],
                'name': result[0][1],
                'age': result[0][2],
                'total_spending': result[0][3]
            }

            return jsonify(user_data)

    except Exception as e:
        print("Unexpected error:", str(e))
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route('/total_spent', methods=['GET'])
def get_total_spent():
    age_range = request.args.get('age_range')

    if not age_range:
        return jsonify({'error': 'Missing age_range parameter'}), 400

    try:
        min_age, max_age = map(int, age_range.split('-'))
    except ValueError:
        return jsonify({'error': 'Invalid age_range format'}), 400

    query = '''
    SELECT ui.age, us.money_spent
    FROM user_info ui
    INNER JOIN user_spending us ON ui.user_id = us.user_id
    '''
    user_data = query_db(query)

    total_spent = 0
    count = 0

    for age, money_spent in user_data:
        if min_age <= age <= max_age:
            total_spent += money_spent
            count += 1

    average_spending = total_spent / count if count > 0 else 0

    return jsonify({"age_range": age_range, "average_spending": average_spending})

# @app.route('/write_to_mongodb', methods=['POST'])
# def write_to_mongodb():
#     if not request.is_json:
#         return jsonify({'error': 'Invalid content type'}), 400

#     data = request.get_json()
#     if not all(key in data for key in ('user_id', 'money_spent')):
#         return jsonify({'error': 'Invalid data'}), 400

#     try:
#         user_id = int(data.get('user_id'))
#         money_spent = float(data.get('money_spent'))
#     except (ValueError, TypeError):
#         return jsonify({'error': 'Invalid data'}), 400

#     result_id = insert_to_mongodb(user_id, money_spent)
#     return jsonify({'message': 'Spending added', 'spending_id': result_id}), 201

if __name__ == "__main__":
    app.run(debug=True)
