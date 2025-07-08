# app.py
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
import uuid
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 请替换为安全的随机密钥

# 配置DeepSeekR1 API
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # 请替换为实际API地址
DEEPSEEK_API_KEY = "your-api-key-here"  # 请替换为您的API密钥

# 模拟用户数据库
users = {
    "testuser": {
        "password": "testpassword",
        "username": "测试用户",
        "email": "test@example.com",
        "avatar": "https://picsum.photos/id/64/200/200",
        "registration_date": "2023-01-01"
    }
}

# 模拟聊天历史数据库
chat_histories = {}


# 登录验证
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username in users and users[username]['password'] == password:
        session['username'] = username
        return jsonify({
            'code': 200,
            'message': '登录成功',
            'user': {
                'username': users[username]['username'],
                'email': users[username]['email'],
                'avatar': users[username]['avatar'],
                'registration_date': users[username]['registration_date']
            }
        })
    else:
        return jsonify({
            'code': 401,
            'message': '用户名或密码错误'
        }), 401


# 检查用户是否已登录
@app.route('/api/check_login', methods=['GET'])
def check_login():
    if 'username' in session:
        username = session['username']
        return jsonify({
            'code': 200,
            'message': '用户已登录',
            'user': {
                'username': users[username]['username'],
                'email': users[username]['email'],
                'avatar': users[username]['avatar'],
                'registration_date': users[username]['registration_date']
            }
        })
    else:
        return jsonify({
            'code': 401,
            'message': '用户未登录'
        }), 401


# 登出
@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({
        'code': 200,
        'message': '登出成功'
    })


# 获取用户信息
@app.route('/api/user_info', methods=['GET'])
def user_info():
    if 'username' in session:
        username = session['username']
        return jsonify({
            'code': 200,
            'user': users[username]
        })
    else:
        return jsonify({
            'code': 401,
            'message': '用户未登录'
        }), 401


# 创建新聊天会话
@app.route('/api/new_chat', methods=['POST'])
def new_chat():
    if 'username' in session:
        username = session['username']
        chat_id = str(uuid.uuid4())

        # 初始化新的聊天会话
        if username not in chat_histories:
            chat_histories[username] = []

        chat_histories[username].append({
            'id': chat_id,
            'title': '新对话',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'messages': []
        })

        return jsonify({
            'code': 200,
            'chat_id': chat_id
        })
    else:
        return jsonify({
            'code': 401,
            'message': '用户未登录'
        }), 401


# 获取聊天历史
@app.route('/api/chat_history', methods=['GET'])
def chat_history():
    if 'username' in session:
        username = session['username']
        if username in chat_histories:
            return jsonify({
                'code': 200,
                'chats': chat_histories[username]
            })
        else:
            return jsonify({
                'code': 200,
                'chats': []
            })
    else:
        return jsonify({
            'code': 401,
            'message': '用户未登录'
        }), 401


# 获取单个聊天会话
@app.route('/api/chat/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    if 'username' in session:
        username = session['username']
        if username in chat_histories:
            for chat in chat_histories[username]:
                if chat['id'] == chat_id:
                    return jsonify({
                        'code': 200,
                        'chat': chat
                    })

        return jsonify({
            'code': 404,
            'message': '聊天会话不存在'
        }), 404
    else:
        return jsonify({
            'code': 401,
            'message': '用户未登录'
        }), 401


# 更新聊天标题
@app.route('/api/chat/<chat_id>/title', methods=['PUT'])
def update_chat_title(chat_id):
    if 'username' in session:
        username = session['username']
        data = request.json
        new_title = data.get('title')

        if username in chat_histories:
            for chat in chat_histories[username]:
                if chat['id'] == chat_id:
                    chat['title'] = new_title
                    return jsonify({
                        'code': 200,
                        'message': '标题更新成功'
                    })

        return jsonify({
            'code': 404,
            'message': '聊天会话不存在'
        }), 404
    else:
        return jsonify({
            'code': 401,
            'message': '用户未登录'
        }), 401


# 删除聊天会话
@app.route('/api/chat/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    if 'username' in session:
        username = session['username']

        if username in chat_histories:
            chat_histories[username] = [chat for chat in chat_histories[username] if chat['id'] != chat_id]
            return jsonify({
                'code': 200,
                'message': '聊天会话已删除'
            })

        return jsonify({
            'code': 404,
            'message': '聊天会话不存在'
        }), 404
    else:
        return jsonify({
            'code': 401,
            'message': '用户未登录'
        }), 404


# 发送消息并获取AI回复
@app.route('/api/chat/<chat_id>/message', methods=['POST'])
def send_message(chat_id):
    if 'username' in session:
        username = session['username']
        data = request.json
        user_message = data.get('message')

        if not user_message:
            return jsonify({
                'code': 400,
                'message': '消息不能为空'
            }), 400

        if username in chat_histories:
            for chat in chat_histories[username]:
                if chat['id'] == chat_id:
                    # 添加用户消息到对话历史
                    user_msg_obj = {
                        'role': 'user',
                        'content': user_message,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    chat['messages'].append(user_msg_obj)

                    # 准备发送给DeepSeek API的消息列表
                    messages = [
                        {'role': msg['role'], 'content': msg['content']}
                        for msg in chat['messages']
                    ]

                    try:
                        # 模拟调用DeepSeek API（实际使用时请替换为真实API调用）
                        # 以下是模拟响应
                        ai_message = f"这是AI的回复：我理解您的问题是关于 '{user_message[:20]}...'。在实际应用中，这里将调用DeepSeek API获取真实回复。"

                        # 添加AI回复到对话历史
                        ai_msg_obj = {
                            'role': 'assistant',
                            'content': ai_message,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        chat['messages'].append(ai_msg_obj)

                        return jsonify({
                            'code': 200,
                            'message': ai_message
                        })
                    except Exception as e:
                        # 如果发生异常，添加一个默认回复
                        error_msg = f"发生错误: {str(e)}"
                        ai_msg_obj = {
                            'role': 'assistant',
                            'content': error_msg,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        chat['messages'].append(ai_msg_obj)

                        return jsonify({
                            'code': 500,
                            'message': error_msg
                        }), 500

        return jsonify({
            'code': 404,
            'message': '聊天会话不存在'
        }), 404
    else:
        return jsonify({
            'code': 401,
            'message': '用户未登录'
        }), 404


# 主页 - 重定向到登录页
@app.route('/')
def index():
    return redirect(url_for('login_page'))


# 登录页面
@app.route('/login')
def login_page():
    return render_template('login.html')


# 个人中心页面
@app.route('/home')
def home_page():
    if 'username' in session:
        return render_template('home.html')
    else:
        return redirect(url_for('login_page'))


# 聊天页面
@app.route('/chat')
def chat_page():
    if 'username' in session:
        return render_template('chat.html')
    else:
        return redirect(url_for('login_page'))


# 聊天历史页面
@app.route('/chat/history')
def chat_history_page():
    if 'username' in session:
        return render_template('chat_history.html')
    else:
        return redirect(url_for('login_page'))


# 特定聊天会话页面
@app.route('/chat/<chat_id>')
def specific_chat_page(chat_id):
    if 'username' in session:
        return render_template('chat.html', chat_id=chat_id)
    else:
        return redirect(url_for('login_page'))


if __name__ == '__main__':
    app.run(debug=True)