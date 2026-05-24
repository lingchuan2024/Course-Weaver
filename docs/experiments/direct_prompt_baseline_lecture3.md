# 第三讲：线性回归的统计视角

## 一、本讲知识地图

本讲从**统计学的角度**重新审视线性回归，核心要回答三个问题：
1. 为什么最小化均方误差（MSE）是合理的？—— 频率学派用最大似然估计给出答案
2. 模型的预测误差从何而来？—— 偏差-方差分解揭示误差的三大来源
3. 如何防止模型过拟合？—— 岭回归从正则化和贝叶斯两个角度给出方案

学完本讲，你应该能理解：**损失函数的选择不是任意的，它隐含了对噪声分布的假设；模型的泛化能力取决于偏差和方差的平衡；正则化等价于给参数加上先验分布。**

---

## 二、从线性代数到概率：为什么 MSE 是合理的？

### 2.1 回顾：线性回归的代数形式

给定数据：
- 特征矩阵 $X \in \mathbb{R}^{N \times D}$（$N$ 个样本，$D$ 维特征）
- 标签向量 $y \in \mathbb{R}^N$

线性回归模型为：
$$y = X\theta + \epsilon$$

其中 $\epsilon$ 是噪声项。在代数视角下，我们直接最小化残差平方和：
$$\min_\theta \|y - X\theta\|_2^2$$

这个目标函数看起来是“凭直觉”选的——我们想让预测值接近真实值。但**为什么是平方损失而不是绝对值损失？为什么不是四次方？**

### 2.2 统计视角：给噪声一个分布

统计建模的关键一步是**对噪声建模**。假设噪声服从高斯分布：
$$\epsilon \sim \mathcal{N}(0, \sigma^2)$$

这意味着什么？对于给定的输入 $x$，输出 $y$ 不再是确定值，而是一个随机变量：
$$y = x^T\theta + \epsilon \quad \Rightarrow \quad y \sim \mathcal{N}(x^T\theta, \sigma^2)$$

**核心理解**：我们不是在拟合一条确定的直线，而是在拟合一个**条件概率分布** $p(y|x,\theta)$。给定 $x$ 和参数 $\theta$，$y$ 的分布是以 $x^T\theta$ 为中心、$\sigma^2$ 为方差的正态分布。

### 2.3 最大似然估计（MLE）：从概率到损失函数

**问题**：如何根据观测数据 $\{(x_n, y_n)\}_{n=1}^N$ 学习参数 $\theta$？

**频率学派的思路**：参数 $\theta$ 是未知的确定值，我们寻找一个 $\theta$，使得**观测到当前数据的概率最大**。

**推导步骤**：

**第1步**：写出单个样本的似然函数
$$p(y_n|x_n, \theta) = \frac{1}{\sqrt{2\pi}\sigma} \exp\left(-\frac{(y_n - x_n^T\theta)^2}{2\sigma^2}\right)$$

**第2步**：假设样本独立同分布（i.i.d.），总似然为乘积
$$L(\theta) = \prod_{n=1}^N p(y_n|x_n, \theta)$$

**第3步**：取对数简化计算（对数似然）
$$\log L(\theta) = \sum_{n=1}^N \log p(y_n|x_n, \theta) = -\frac{1}{2\sigma^2}\sum_{n=1}^N (y_n - x_n^T\theta)^2 - N\log(\sqrt{2\pi}\sigma)$$

**第4步**：最大化对数似然等价于最小化 MSE
$$\max_\theta \log L(\theta) \quad \Leftrightarrow \quad \min_\theta \sum_{n=1}^N (y_n - x_n^T\theta)^2 = \min_\theta \|y - X\theta\|_2^2$$

**关键洞察**：MSE 不是随意选的！它是在**高斯噪声假设**下最大似然估计的自然结果。如果噪声服从拉普拉斯分布，损失函数就会变成绝对值损失（L1 loss）。

---

## 三、频率学派 vs 贝叶斯学派：两种世界观

在继续深入之前，必须理清两种统计范式的根本区别。

| 对比维度 | 频率学派（Frequentist） | 贝叶斯学派（Bayesian） |
|---------|----------------------|----------------------|
| **对参数 $\theta$ 的看法** | 未知的**确定值** | **随机变量**，服从某个分布 |
| **推断目标** | 点估计：$\hat{\theta}_{MLE} = \arg\max_\theta P(X\|\theta)$ | 后验分布：$P(\theta\|X) \propto P(X\|\theta)P(\theta)$ |
| **核心工具** | 最大似然估计（MLE） | 最大后验估计（MAP）、变分推断、MCMC |
| **先验信息** | 不使用 | 通过 $P(\theta)$ 引入 |
| **优势** | 计算简单，无需设计先验 | 小样本下更稳健，能量化不确定性 |
| **劣势** | 稀疏数据下容易过拟合 | 先验设计困难，计算量大 |

**常见误解澄清**：
- MLE 不是“不考虑不确定性”，频率学派也有置信区间，但构建方式不同
- 贝叶斯方法在大样本下会趋近 MLE（先验的影响随数据量增加而衰减）

---

## 四、偏差与方差：理解泛化误差的钥匙

### 4.1 基本概念

在讨论模型性能时，我们需要区分两个层面的“参数”：
- **真实参数** $\theta$：数据生成过程的真实参数（未知）
- **估计参数** $\hat{\theta}$：从数据中学到的参数（随机变量，因为数据是随机的）

**偏差（Bias）**：估计量的期望与真实值的差距
$$\text{Bias}(\hat{\theta}) = \mathbb{E}_{X|\theta}[\hat{\theta}] - \theta$$

**方差（Variance）**：估计量自身的波动程度
$$\mathbb{V}[\hat{\theta}] = \mathbb{E}_{X|\theta}[(\hat{\theta} - \mathbb{E}[\hat{\theta}])^2]$$

**无偏估计**：$\text{Bias} = 0$，即估计量的期望等于真实值。

### 4.2 经典例子：方差估计为什么除以 n-1？

**问题**：已知 $N$ 个独立同分布样本 $X_1, ..., X_N$，均值为 $\mu$，方差为 $\sigma^2$。样本方差 $\hat{\sigma}^2 = \frac{1}{N}\sum_{n=1}^N (X_n - \hat{\mu})^2$ 是有偏还是无偏？

**推导**（关键步骤）：

$$\begin{aligned}
\mathbb{E}[\hat{\sigma}^2] &= \mathbb{E}\left[\frac{1}{N}\sum_{n=1}^N (X_n - \hat{\mu})^2\right] \\
&= \mathbb{E}\left[\frac{1}{N}\sum_{n=1}^N ((X_n - \mu) - (\hat{\mu} - \mu))^2\right] \\
&= \mathbb{E}\left[\frac{1}{N}\sum_{n=1}^N (X_n - \mu)^2\right] - \mathbb{E}[(\hat{\mu} - \mu)^2] \\
&= \sigma^2 - \frac{\sigma^2}{N} = \frac{N-1}{N}\sigma^2
\end{aligned}$$

**结论**：$\hat{\sigma}^2$ 低估了真实方差，偏差为 $-\sigma^2/N$。无偏估计应修正为：
$$\hat{\sigma}^2_{unbiased} = \frac{1}{N-1}\sum_{n=1}^N (X_n - \hat{\mu})^2$$

**直觉理解**：我们用样本均值 $\hat{\mu}$ 代替真实均值 $\mu$，这消耗了一个自由度，使得残差平方和“看起来”比实际小。

### 4.3 偏差-方差分解：预测误差的三大来源

对于新样本 $x$，预测的期望均方误差可以分解为：

$$\begin{aligned}
\mathbb{E}[(y - f_{\hat{\theta}}(x))^2] &= \mathbb{E}[(f_\theta(x) + \epsilon - f_{\hat{\theta}}(x))^2] \\
&= \underbrace{\sigma^2}_{\text{不可约噪声}} + \underbrace{(f_\theta(x) - \mathbb{E}[f_{\hat{\theta}}(x)])^2}_{\text{偏差}^2} + \underbrace{\mathbb{E}[(f_{\hat{\theta}}(x) - \mathbb{E}[f_{\hat{\theta}}(x)])^2]}_{\text{方差}}
\end{aligned}$$

**三项含义**：
1. **不可约噪声** $\sigma^2$：数据本身的随机性，任何模型都无法消除
2. **偏差²**：模型平均预测与真实值的差距，反映模型**拟合能力**
3. **方差**：模型预测的波动性，反映模型对数据**敏感度**

**推导关键步骤**（理解为什么交叉项消失）：
- 展开平方时，交叉项为 $2\mathbb{E}[(f_\theta - \mathbb{E}[f_{\hat{\theta}}])(\mathbb{E}[f_{\hat{\theta}}] - f_{\hat{\theta}})]$
- 注意 $\mathbb{E}[f_{\hat{\theta}}]$ 是常数，$f_\theta$ 也是常数（真实函数）
- 因此 $\mathbb{E}[\mathbb{E}[f_{\hat{\theta}}] - f_{\hat{\theta}}] = 0$，交叉项期望为零

---

## 五、过拟合与欠拟合：偏差-方差的直观体现

### 5.1 现象定义

| 现象 | 模型复杂度 vs 数据复杂度 | 偏差 | 方差 | 表现 |
|------|------------------------|------|------|------|
| **欠拟合** | 模型太简单 | 高 | 低 | 训练集和测试集误差都大 |
| **过拟合** | 模型太复杂 | 低 | 高 | 训练集误差小，测试集误差大 |

### 5.2 过拟合的两种成因

**情况1**：模型本身不合理地复杂（如用100次多项式拟合线性数据）
→ 解决方案：简化模型结构

**情况2**：模型复杂度合理，但数据不足（更常见）
→ 解决方案：
- 训练策略：早停（early stop）、Dropout、随机梯度下降
- 引入正则化：给参数施加约束

---

## 六、岭回归：正则化的经典案例

### 6.1 优化视角：给损失函数加惩罚项

岭回归的目标函数：
$$\min_\theta \underbrace{\|y - X\theta\|_2^2}_{\text{数据拟合}} + \lambda \underbrace{\|\theta\|_2^2}_{\text{参数惩罚}}$$

**$\lambda$ 的作用**：
- $\lambda = 0$：退化为普通线性回归
- $\lambda \to \infty$：$\theta \to 0$，模型变成常数预测
- $\lambda$ 适中：平衡拟合精度和参数大小

**闭式解推导**：
$$\frac{\partial L}{\partial \theta} = 2X^T(X\theta - y) + 2\lambda\theta = 0$$
$$\Rightarrow (X^TX + \lambda I)\theta = X^Ty$$
$$\Rightarrow \hat{\theta}_{ridge} = (X^TX + \lambda I)^{-1}X^Ty$$

**关键理解**：加上 $\lambda I$ 后，即使 $X^TX$ 不可逆（特征数多于样本数时常见），矩阵也变成可逆的。这就是“岭”（ridge）名称的由来——在对角线上加了一个“山脊”。

### 6.2 贝叶斯视角：参数先验的威力

**贝叶斯公式**：
$$P(\theta|X, y) \propto \underbrace{P(y|X, \theta)}_{\text{似然}} \cdot \underbrace{P(\theta)}_{\text{先验}}$$

**假设**：
- 似然：$y = x^T\theta + \epsilon, \quad \epsilon \sim \mathcal{N}(0, \sigma^2)$
- 先验：$\theta \sim \mathcal{N}(0, \gamma^2 I)$（参数服从零均值高斯分布）

**MAP 推导**：
$$\begin{aligned}
\hat{\theta}_{MAP} &= \arg\max_\theta \log P(y|X,\theta) + \log P(\theta) \\
&= \arg\min_\theta \frac{1}{2\sigma^2}\|y - X\theta\|_2^2 + \frac{1}{2\gamma^2}\|\theta\|_2^2 \\
&= \arg\min_\theta \|y - X\theta\|_2^2 + \underbrace{\frac{\sigma^2}{\gamma^2}}_{\lambda}\|\theta\|_2^2
\end{aligned}$$

**惊人结论**：岭回归的 L2 正则化等价于给参数加上高斯先验！正则化系数 $\lambda = \sigma^2/\gamma^2$：
- 噪声大（$\sigma^2$ 大）→ $\lambda$ 大 → 更不相信数据，强正则化
- 先验方差大（$\gamma^2$ 大）→ $\lambda$ 小 → 先验信息弱，弱正则化

### 6.3 两种视角的对比

| 视角 | 岭回归的理解 | 优化目标 |
|------|------------|---------|
| **频率学派（正则化）** | 在损失函数上加惩罚项，防止参数过大 | $\min_\theta \|y-X\theta\|^2 + \lambda\|\theta\|^2$ |
| **贝叶斯学派（MAP）** | 参数有先验分布，通过后验最大化学习 | $\max_\theta P(y\|X,\theta)P(\theta)$ |

**常见误解**：正则化不是“让参数变小”，而是“在数据不足时，让参数向0收缩”。当数据充足时，似然项主导，正则化影响减弱。

---

## 七、总结与知识串联

本讲的核心逻辑链：

1. **噪声假设** → **似然函数** → **损失函数**
   - 高斯噪声 → MLE → MSE 损失
   - 拉普拉斯噪声 → MLE → L1 损失

2. **估计量的性质** → **泛化误差分解**
   - 偏差：模型平均预测与真实的差距
   - 方差：模型对数据波动的敏感度
   - 噪声：不可消除的固有误差

3. **过拟合的根源** → **正则化的必要**
   - 高方差 → 对训练数据过敏感 → 泛化差
   - 正则化 → 限制参数空间 → 降低方差

4. **正则化的两种解释**
   - 优化视角：加惩罚项约束参数大小
   - 贝叶斯视角：引入先验分布表达偏好

**下讲预告**：将线性回归推广到广义线性模型（GLM），并学习模型选择策略。

---

## 八、课后作业提示

作业要求完成两个编程实验和一份技术报告。报告部分的关键点：

**问题1**：数据依赖的噪声模型
$$y = \sum_{d=1}^D x^{d-1}\theta_d + \epsilon, \quad p(\epsilon|x) = \frac{1}{\sqrt{2\pi x^2}}\exp\left(-\frac{\epsilon^2}{2x^2}\right)$$

注意：这里噪声方差是 $x^2$，即**异方差**（heteroscedastic）。MLE 推导时，对数似然中的 $\sigma^2$ 要替换为 $x^2$，最终损失函数会变成加权最小二乘。

**问题2**：拉普拉斯先验
$$p(\theta_d) = \frac{1}{2b_d}\exp\left(-\frac{|\theta_d|}{b_d}\right)$$

MAP 推导会得到 L1 正则化项（Lasso 回归），与高斯先验得到 L2 正则化形成对比。注意拉普拉斯分布的对数包含绝对值，不可导，需要用次梯度方法优化。
