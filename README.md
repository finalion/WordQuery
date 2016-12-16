# WordQuery 插件(anki)

[Introduction in English](introduction.md) *contributed by Li Tan*.

## 写在前面

本插件最初只设想了在线查询单词释义的功能，目的是方便自己在阅读文献查阅文档时快速自动把生词释义添加到anki。在实现过程中，很多朋友提出了非常好的意见，因此插件功能也日渐增多，日益完善。

当然很多人相对自动制卡更喜欢手动制卡，这是anki的初衷。对需要通过各种英语考试的学生来言，学习、熟识和掌握单词是关键的，手动制卡更能加深对单词的理解；对平常需要阅读大量外文文档、新闻和文献的人，自动制卡能很好的提高工作效率。

本人非专业软件开发人员，开发时间和代码编写能力有限，插件肯定存在大量的缺陷和问题。如果您有更好的想法实现或者代码问题的修正，欢迎共同完善本项目：
[https://github.com/finalion/WordQuery](https://github.com/finalion/WordQuery)

在您使用过程中出现的任何问题也可通过以下方式随时交流：

> **Email: finalion@gmail.com** (the best)   
*QQ: 9610968*

## 安装方式
     
1. [https://github.com/finalion/WordQuery](https://github.com/finalion/WordQuery)下载并放到anki插件文件夹
2. 安装代码775418273

## 主要功能

1. 快速零散制卡      
    在添加卡片和编辑卡片界面，输入单词，通过快捷键、按钮或右键菜单可直接获取详细释义，并自动填充各字段，实现快速制卡。   
2. 批量制卡  
    浏览器界面中，选择多个单词，通过快捷键、按钮或右键菜单可直接获取详细释义，并自动填充各字段，实现批量快速制卡。 

## 使用参考

1. “工具”菜单-->"Word Query"，弹出设置界面
    - 点击“选择笔记类型”按钮，设定笔记模板；
    - 点击“mdx文件夹按钮”，弹出mdx设定界面，增加mdx字典文件夹，支持递归查找。

2. 支持多种字典的扩展
    - mdx字典：设置字典所在的文件夹，自动索引字典生成映射项；
    - 网络字典：支持网络字典的多个字段插入，目前插件内置有道词典和迷你海词；
    - *mdx服务：也属于网络字典，但目前可在字典列表中选择该项后，快速添加服务器地址。*

    所有字典以插件服务形式实现，用户可自己编写适合自己需求的插件。插件实现方式可参考。

3.  插件对Anki界面的修改，可在多种编辑模式下快速查询并添加单词释义。
    - “添加笔记”界面增加了“Query”按钮；
    - 在主界面和浏览界面增加了工具栏菜单“WoryQuery”；
    - 在编辑器右键菜单中增加了“Query”菜单项和“Query Current”菜单项。

    所有操作目前支持快捷键"Ctrl+Q"。


3. 参考截图

![](screenshots/add_dict_folders.png)

![](screenshots/note_type.png)

![](screenshots/dicts.png)

![](screenshots/editor.png)

![](screenshots/browser.png)

## 字典服务插件定义

#### 实现Service类

1. 词典标签定义，定义静态变量 ```__register_label__```  
   词典标签将出现在字典下拉列表中。

#### 实现导出字典字段函数

1. ```@export(fld_name, order)``` 修饰导出字典字段函数；
2. 装饰器参数```fld_name```为字典字段名称，出现在字典字段下拉列表中；
3. 装饰器参数```order```为字典字段在下拉列表中的顺序，小号在上，大号在下。

#### 添加字段样式（可选）
1. ```@with_style(**kwargs)```修饰导出字典字段函数；
2. 目前支持的可选参数包括```css```和```js```，其中css样式将插入到字典字段中，js代码将插入到笔记模板中。

具体可参考有道词典和海词实现方式。    

## 已知问题

1. 编辑器中第一次查询有时候取不到数据；有时获取的查询单词为空。

## 参考
- mdx 解析：  [mmjang](https://github.com/mmjang/mdict-query)
- mdx server：  [你家老黄](https://ninja33.github.io/) 
- goldendict
