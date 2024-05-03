## 一、数据库

'instance/logs.db'

## 二、导入

1. 导出[bondage club tools](https://chromewebstore.google.com/detail/bondage-club-tools/pgigbkbcecbpgijnfhmpmkipgondpnpc)数据库 (Options - Data - Export database)
2. 将zip包中的chatRoomLogs放入项目的import_logs目录下
3. 执行 `make import` 或者 `python3 import_json.py`

## 三、使用

### 1. 本地执行
1. `make run`
2. 访问[用户列表](http://127.0.0.1:5000/users)

### 2. 部署执行
1. `make docker`
2. 访问[服务器](http://docker-ip:9999/users)


## 四、关联API接口

### 1. 用户查询

URL: [http://127.0.0.1:5000/user/{some-user}]
    
将`{some-user}`改成你需要检索的`UserID`或`UserName`


### 2. 列出用户相关的会话

URL: [http://127.0.0.1:5000/id/{UserID}/session]

或从上述[用户界面](#用户查询)直接进入

### 3. 获取会话

URL: [http://127.0.0.1:5000/s/{session}]

将`{session}`改成你需要进入的`session`

或从上述[Session列表](#列出用户相关的对话)直接进入

注：url中加入`?raw`参数可直接获取Json细节。如[http://127.0.0.1:5000/s/elLGYp4lWQll-FOQAKJm?raw]

### 4. 删除会话

在对应的会话末尾有一个`删除`按钮，点击并`确认`即可

### 5. 清除冗余

例子：从第`4000`条log开始，检查3000条（`3`*1000）

[http://127.0.0.1:5000/dedup/4000?p=3]


## 五、参数
|参数|说明|
|--|--|
|del=1|确认删除session|
|raw=1|显示原始JSON|
|limit=50|显示每页显示Log数|
|page=1|跳转页数|


## 鸣谢
仅以此项目献给那些陪伴在我身边的有趣灵魂们：

Qqq (112684), halaxi (70391), Ruth (115625), minu (120172), migo (85068),

sandy (126316), KYA (150000), ting (119738), keke (76118)

yanke (88252), Hazel (135377), bella (137787), cc (84122), lisaa (82147), kawaii ran (91054), Chloe (153983)

kokoro (139498)