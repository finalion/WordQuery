# query word plugin for anki

## 主要功能

1. 在添加卡片界面，直接从在线词典取简单释义，从mdx词典取详细释义
2. 批量导入单词表，自动查询添加卡片。

目前支持词典：
 - Collins COBUILD中文
 - Collins COBUILD英文
 - Oxford Dictionary of English 3e
 - 牛津高阶词典第8版
 - Merriam-Webster's Collegiate Dictionary and Thesaurus, 2015
 - MacmillanEnEn
 - Longman Contemporary English 6th

![](screenshots/demo.gif)

## 安装
- 下载wordquery.py和mdict文件夹到anki插件目录
- 或者，anki中使用代码775418273安装（不能保证及时更新）

## 使用

- 本插件需要模板支持，在anki中导入templates文件下的apkg文件
- “工具”菜单-->"word query"，设置词典文件的路径或者mdx服务器地址
- 添加新的卡片时，通过“Query”按钮或“Ctrl+Q”快捷键，从词典中读取填充释义
- “文件菜单”-->"Batch Import..."，打开单词列表，自动查询并添加卡片


## 感谢
- 模板在[你家老黄](https://ninja33.github.io/)基础上修改
- mdx解析工具由[mmjang](https://github.com/mmjang/mdict-query)提供