# WordQuery 插件(anki)

## 主要功能

1. 快速零散制卡      

    在添加卡片界面，输入单词，可直接获取详细释义，并自动填充各字段，实现快速制卡。   

2. 批量制卡  

    批量导入单词表，自动获取单词释义并添加卡片。


## 安装
     
1. [https://github.com/finalion/anki](https://github.com/finalion/anki)下载并放到anki插件文件夹

2. 安装代码775418273
    

## 使用

1. “工具”菜单-->"Word Query"，弹出设置界面，点击“选择笔记类型”按钮，设定笔记模板

3. 对笔记模板的每个字段设定是否需要使用字典，以及字典路径

   字典路径可以为本地mdx文件，也可以设置为远程mdx server地址。mdx server部署方式：  

    - [你家老黄](https://ninja33.github.io/) - MDX server  

    - [mmjang](https://github.com/mmjang/mdict-query) -  mdict-query


2. 添加新单词卡片  
 
   在添加卡片界面，第一个文本框输入单词后，按下“查询”按钮或者使用“Ctrl+Q”快捷键，可从设置的字典中获取释义。

3. 卡片浏览器

    - 选中要更新释义的单词，编辑器中右键菜单中点击“Query”或者使用“Ctrl+Q”快捷键，从设置的字典中更新相关字段释义。

    - 一次选中多个单词，浏览器Word Query菜单中，点击“Query” 或者使用“Ctrl+Q”快捷键，批量对单词释义进行更新。


## 感谢
- 模板在[你家老黄](https://ninja33.github.io/)基础上修改
- mdx解析工具由[mmjang](https://github.com/mmjang/mdict-query)提供

