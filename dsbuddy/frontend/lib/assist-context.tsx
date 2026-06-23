"use client";

import { createContext, useContext, useState, type ReactNode } from "react";

const AssistContext = createContext<{ on: boolean; toggle: () => void }>({
  on: false,
  toggle: () => {},
});

export function AssistProvider({ children }: { children: ReactNode }) {
  const [on, setOn] = useState(false);
  return (
    <AssistContext.Provider value={{ on, toggle: () => setOn((v) => !v) }}>
      {children}
    </AssistContext.Provider>
  );
}

export function useAssist() {
  return useContext(AssistContext);
}

export const TERM_DEFINITIONS: Record<string, string> = {
  skewness:
    "How lopsided your data is. A positive value means a long tail to the right; negative means left. Values above 2 or below −2 usually need attention before modeling.",
  correlation:
    "How closely two columns move together. Ranges from −1 (opposite) to +1 (identical). Near 0 means no linear relationship.",
  "pearson correlation":
    "A specific way to measure linear correlation. It assumes both columns are roughly normally distributed.",
  "mutual information":
    "How much knowing one column reduces uncertainty about another. Unlike correlation, it captures non-linear relationships too.",
  outlier:
    "A data point that sits unusually far from the rest of the data. We detect these using the IQR method — anything beyond 1.5× the interquartile range.",
  IQR: "Interquartile Range — the span between the 25th and 75th percentile values. A robust way to measure spread that ignores extreme values.",
  "missing value":
    "A blank or null entry in your dataset. A small number is normal; over 30% in a column usually means you need a strategy (impute or drop).",
  cardinality:
    "The number of unique values in a column. High cardinality in a categorical column (e.g. 10,000 unique city names) can be problematic for some models.",
  leakage:
    "When a column contains information that wouldn't be available at prediction time — like including 'discharge date' when predicting hospital readmission. It makes your model look great in testing but fail in production.",
  multicollinearity:
    "When two or more columns are so correlated they're basically measuring the same thing. This confuses some models and inflates feature importance scores.",
  "class imbalance":
    "When one category has far more examples than others — e.g. 95% 'Not fraud' and 5% 'Fraud'. Models trained on imbalanced data often just predict the majority class.",
  "standard deviation":
    "How spread out the values are around the mean. A low std means values cluster tightly; a high std means they're spread wide.",
  variance: "Standard deviation squared. Measures how spread out values are. Columns with near-zero variance carry almost no information.",
  MAR: "Missing At Random — the fact that a value is missing is related to other columns you can observe, but not to the missing value itself. Usually safe to impute.",
  MCAR: "Missing Completely At Random — missingness has no pattern at all. The safest kind.",
  MNAR: "Missing Not At Random — the value is missing because of the missing value itself (e.g. sick patients not reporting health scores). Hardest to handle correctly.",
  "cross-validation":
    "A technique to estimate model accuracy more reliably. We split the data into 3 folds, train on 2, test on 1, repeat 3 times, and average the results.",
  accuracy: "The percentage of predictions that were correct. Simple, but misleading on imbalanced datasets.",
  "f1 score":
    "A balance between precision (don't cry wolf) and recall (catch everything). Better than accuracy when classes are imbalanced.",
  AUC: "Area Under the ROC Curve. Measures how well the model separates the two classes regardless of which threshold you pick. 0.5 = random, 1.0 = perfect.",
  "r2": "How much of the target's variation your model explains. 1.0 = perfect; 0 = no better than predicting the mean; negative = worse than the mean.",
  RMSE: "Root Mean Squared Error — the average size of your prediction errors, in the same units as the target. Lower is better.",
};
