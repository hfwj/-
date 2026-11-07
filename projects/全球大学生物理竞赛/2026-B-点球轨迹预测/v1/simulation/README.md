# 点球模型复算

这是代表性算例和多解情景演示，尚未实现完整的概率预测。Python 3.12 环境下已复算。

在本目录中运行：

```bash
python -m pip install -r requirements.txt
python penalty_model.py --output ../results/data/scenarios.json
```

输出包含各情景的初速度、有效阻力参数、有效旋转向量、观测拟合残差及球门平面交点。改变的是 `Omega` 沿早期速度方向的分量，其他参数重新拟合。

模型使用 SciPy `solve_ivp` 积分、`least_squares` 拟合，使用球门事件 `x=11` 及球心触地事件 `z=0.11`。若先触地，输出 `goal_reached=false`，意味着需要反弹模型，不能直接断言该球必定不进门。

限制：无风、常系数、先触地后不继续模拟；观测拟合成功不代表模型已获实测验证。现有 `validation.json` 记录解析极限与步长检查，不代表95%预测区域已经校准。
