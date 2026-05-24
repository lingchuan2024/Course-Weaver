# Lecture3 生成笔记质量测试

测试对象：`output/lecture3-deepseek/notes/01_lecture_notes.md`

测试目标：评估生成笔记是否像自然讲义，尤其关注章节顺序、过渡自然度、模板感和噪声控制。

## 1. 测试方法

本次使用两类检查：

1. 本地结构检查：提取所有二级标题，观察章节顺序、重复标题、噪声标题和异常跳转。
2. DeepSeek 助教评审：输入章节目录和相邻章节片段，让模型从课程助教视角评价“学习路径是否自然”。

## 2. 总体结论

单个章节的正文质量已经明显优于普通摘要，尤其是线性回归、MLE、均值方差、Ridge Regression 等章节，能解释动机、符号和公式含义。

但是整体笔记的章节顺序和过渡还不合格。主要问题是后半部分出现碎片化知识点堆叠，导致主线断裂。DeepSeek 评审给出的整体评分为 4/10。

## 3. 过渡自然的部分

前半部分主线比较顺：

```text
Linear Regression example
-> Statistical Modeling
-> Maximum Likelihood Estimation
-> Ordinary Linear Regression
```

统计基础部分也有合理递进：

```text
Random Variables
-> Mean / Covariance / Unbiased Estimation
-> Properties of Mean and Variance
-> Variance of Estimation
-> Bias-Variance Trade-off
```

这些章节内部可读性较好，说明新版 prompt 对单节改写是有效的。

## 4. 主要问题

### 4.1 Homework 插入位置错误

当前顺序中，`Homework 1` 出现在 `Frequentist v.s. Bayesian` 之后，但后面又继续回到 `The Bias of Estimation`。

这会让读者误以为课程已经结束，然后又突然进入前面统计估计部分的细节。

### 4.2 Bias Estimation 被切碎

从 `The Bias of Estimation` 开始，后面出现大量碎片标题：

```text
Formula near The Bias of Estimation
Toy Example 1
Formula near E X|µ [X n ] − µ
Toy Example 2
Formula near 1 N
1 N
▶ The unbiased estimation is σ̂ 2 =
Formula near 1 N−1
Formula near P N
− µ̂) 2 .(What if µ is known?)
```

这些内容本应合并成一个或两个完整章节，例如：

```text
The Bias of Estimation
Detailed Derivation: Bias of Variance Estimator
```

现在的效果像是把课件 block 逐个写成了小节，破坏了讲义感。

### 4.3 重复总结

`In Summary` 出现了两次，说明当前合并逻辑没有识别重复总结页。

### 4.4 根因不是写作 prompt

新版 prompt 已经让单节内容更自然，但无法修复章节级结构问题。根因在：

- 知识点抽取过于碎片化。
- 跨页合并不足。
- note plan 基本按课件顺序追加，没有真正根据知识关系重排。
- Homework、Summary、Next 等页面没有被放入专门的尾部或附录。

## 5. 建议的新顺序

最小可行修复可以不重写正文，先调整章节顺序和合并规则：

```text
一、基础与模型
1. Random Variables and Instances/Samples
2. Recall the Example of Linear Regression
3. The Key of Statistical Modeling
4. A Frequentist Viewpoint: Maximum Likelihood Estimation
5. Key Statistical Analysis for Ordinary Linear Regression

二、统计推断基础
6. Mean, (Co)variance, and Their Unbiased Estimation
7. Properties of Mean and Variance
8. The Variance of Estimation
9. The Bias of Estimation
10. Detailed Derivation: Bias of Variance Estimator

三、模型评估与选择
11. The Trade-off Between Bias and Variance
12. Bias-Variance Trade-off: Model Misspecification
13. Bias-Variance Trade-off: Training Process
14. Overfitting and Underfitting

四、模型改进与统计视角
15. Ridge Regression: MSE with L2 Regularization
16. Ridge Regression: A Bayesian Viewpoint
17. ML: Frequentist Statistic Viewpoint
18. ML: Bayesian Statistic Viewpoint
19. Frequentist v.s. Bayesian

五、总结与作业
20. In Summary
21. Next
22. Model / Feature Selection Strategies
23. Homework
```

## 6. MVP 修复优先级

### P0：先做章节级清洗

- `Homework` 永远放到最后或附录。
- `In Summary` 合并去重。
- `Next` 放在总结之后。
- 标题包含 `Formula near`、孤立公式、孤立数字的 section 不作为主章节，只能并入最近的概念章节。

### P1：做跨页主题合并

把同一页段内的公式、例子、推导并入最近的主题章节，例如：

```text
The Bias of Estimation
  - definition
  - formula derivation
  - toy examples
  - unbiased variance estimator
```

### P2：再做知识关系排序

建立 `prerequisite_of / derives / example_of / contrasts_with` 关系，然后用：

```text
基础概念 -> 模型建立 -> 参数估计 -> 模型评估 -> 模型改进 -> 总结作业
```

作为学习路径生成规则。

## 7. 判断

当前版本适合展示“单节改写质量”和“可追溯结构”，但还不适合宣称已经实现了“按学习路径重构整份课件”。

下一步最值得做的不是继续调 prompt，而是改 `note_plan`：先清洗章节，再合并碎片，最后根据知识关系重排。
