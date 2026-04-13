# SNL 四元组版最小编译器

这个目录提供了一版可运行的 `SNL -> 四元组 -> MIPS` 原型，便于课程实验继续扩展。

## 当前支持的 SNL 子集

- 程序头：`program <id>`
- 变量声明：`var integer ...; char ...;`
- 支持定长数组声明：如 `integer nums[4];`
- 语句：
  - 赋值 `:=`
  - 过程调用 `foo(...)`
  - `read(x)`
  - `write(expr)`
  - `while ... do ... endwh`
  - `if ... then ... else ... fi`
  - `return(expr)`，可用于过程内提前结束
- 表达式：
  - 整数常量
  - 字符常量，如 `'A'`
  - 字符串常量，如 `"Hello\n"`
  - 标识符
  - 数组访问，如 `nums[i]`
  - 一元负号，如 `-x`、`-(1 + 2)`
  - `+ - * /`
  - 条件运算 `< <= > >= = <>`
- 过程声明：
  - `procedure foo(...)`
  - 值参和 `var` 引用参数
  - 过程内局部变量声明
  - 过程嵌套定义与递归调用

## 编译输出

- 词法分析输出：`Token` 序列
- 语法分析输出：层次文本语法树
- 中间代码：四元组 `(op, arg1, arg2, result)`
- 目标代码：`MIPS`

## 运行方式

```bash
python3 main.py examples/demo.snl -o examples/demo.asm --ir-out examples/demo.ir --tokens-out examples/demo.tokens
```

如果需要单独导出语法树：

```bash
python3 main.py examples/demo.snl -o examples/demo.asm --ast-out examples/demo.ast
```

直接编译并运行：

```bash
python3 main.py examples/hello.snl -o examples/hello.asm --run
```

更完整的综合示例：

```bash
python3 main.py examples/advanced.snl -o examples/advanced.asm --run
```

数组示例：

```bash
python3 main.py examples/arrays.snl -o examples/arrays.asm --run
```

过程示例：

```bash
python3 main.py examples/procedures.snl -o examples/procedures.asm --run
```

如果需要给运行阶段传入输入：

```bash
python3 main.py examples/demo.snl -o examples/demo.asm --run --run-input "5\n"
```

说明：

- `write("Hello")` 现在会直接生成字符串输出，不需要拆成多个字符。
- 支持 `<=`、`>=`、`>`、`<>` 和一元负号，示例见 `examples/advanced.snl`。
- 支持定长数组和下标访问，数组在 MIPS 数据段中会分配连续空间。
- 对字面量下标会做编译期越界检查，例如在大小为 `4` 的数组上访问 `nums[4]` 会直接报错。
- 对变量下标会生成运行时越界检查，越界时会在 MARS 中打印错误并终止。
- 编译阶段会做简单常量折叠，例如 `x := -(2 + 3) * 4` 会直接折叠成常量赋值。
- 运行阶段默认会在当前目录寻找 `Mars for Compile 2022.jar`，也可以用 `--mars-jar` 手动指定。
- 当前字符串仅支持用于 `write(...)`，不参与赋值、算术和条件判断。

## 图形界面

```bash
python3 gui.py
```

GUI 支持：

- 编辑或打开 SNL 源程序
- 一键编译并查看 `Tokens / AST / IR / MIPS`
- 配置运行输入并直接调用 MARS 运行
- 载入 `examples/` 里的示例，便于课堂展示

如果本机 `tkinter/Tk` 因系统版本或 Python 打包方式无法启动，可以改用浏览器版 GUI：

```bash
python3 web_gui.py
```

浏览器版 GUI 同样支持：

- 编辑源码并一键编译
- 查看 `Tokens / AST / IR / MIPS`
- 直接运行生成的 MIPS 程序
- 自动加载 `examples/` 示例，适合答辩和课堂展示

## 目前还没覆盖的内容

- `type` 自定义类型
- 更完整的数组类型能力
- `record`
- 更完整的错误恢复

这些部分可以继续在当前结构上往里补，不需要推翻重写。

## 自动化测试

```bash
pytest -q
```
