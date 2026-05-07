# Instructions

## 基本思路
这是一个数据库查询工具，用户可以添加db url，系统会自动连接到数据库，获取数据库的metadata信息，将table和view信息展示出来。用户可以自己输入sql查询，也可以输入自然语言生成sql查询。

基本想法
- 数据库连接字符串和数据库的metadata都会存储到sqlite数据库中。用户可以根据postgresql的功能查询系统中的表和视图信息，用LLM将这些信息转换成json格式，存储到sqlite数据库中。以后可以复用这些信息。