# Titanic analysis project

This module analyzes the Titanic dataset through exploratory data analysis and predictive modeling. The notebook workflow follows a consistent pattern: data quality checks, survival-story exploration, class-imbalance handling, model comparison, regression analysis, and a final deployment recommendation.

## Module-level note

The EDA shows that survival is associated with sex, ticket class, and fare. Women had much higher survival rates than men, higher ticket classes had better survival outcomes, and passengers in the higher-fare range were disproportionately more likely to survive. The fare distribution is right-skewed because the mean is substantially larger than the median and mode, which reflects a long upper tail caused by a minority of very high-ticket passengers. The two strongest numerical relationships are `ticket_class` with `fare` and `siblings_spous` with `parent_children`, showing that class pricing and family group travel patterns are the key drivers in the data. The modeling stage uses a stratified train/test split before preprocessing, fits all preprocessing steps only on the training fold, and compares the same three classifiers on identical data.

### Model comparison table

| Model | Accuracy | Precision | Recall | F1 Score | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Random Forest | 0.8090 | 0.7429 | 0.7647 | 0.7536 | 0.8255 |
| Logistic Regression | 0.8090 | 0.7833 | 0.6912 | 0.7344 | 0.8610 |
| Decision Tree | 0.7584 | 0.6712 | 0.7206 | 0.6950 | 0.7456 |

### Regression metrics

| Model | MAE | RMSE | R² | Adjusted R² |
|---|---:|---:|---:|---:|
| Linear Regression | 18.3920 | 41.3073 | 0.3604 | 0.2649 |

These classification and regression metrics are reported in separate groups because they are measured on different scales and are not directly comparable as one merged metric space.

### Final recommendation

I would deploy the Random Forest classifier for the Titanic survival task. It achieved the highest F1 score among the classifiers at 0.7536, which gives the strongest balance of precision and recall compared with Logistic Regression (0.7344) and the Decision Tree (0.6950). Its accuracy is tied with Logistic Regression at 0.8090, but the Random Forest has stronger recall at 0.7647, which is especially valuable when missing a positive survival case is costly. Although Logistic Regression has the best ROC-AUC at 0.8610, the Random Forest remains the strongest overall choice for this class-imbalanced problem because the task-specific metric most relevant to deployment is F1 score.

## Files in this module

- 01_eda.ipynb — exploratory analysis, missing-value rules, distributions, bivariate and multivariate storytelling, and the EDA-only scaling check
- 02_modeling.ipynb — stratified train/test split, preprocessing pipeline, classifier comparison, imbalance handling, GridSearchCV tuning, regression task, and saved end-to-end pipeline
- titanic.csv — saved offline dataset copy used as the consistent fallback data source for modeling

---

## 1. Exploratory data analysis summary

The EDA notebook starts by loading the Titanic dataset, checking its shape and schema, and computing missing-value percentages across columns. The dataset is then renamed for readability and saved to a local CSV file with `df.to_csv("titanic.csv", index=False)` so the modeling stage can reuse the same processed offline data source.

### Missing-value handling rule

The missing-value strategy follows a percentage-based rule:

- Less than 5% missing: drop the affected rows
- 5% to 30% missing: impute using the column mean for continuous numeric variables
- More than 30% missing: drop the whole column

This rule is applied in the notebook to the relevant columns. For example, `age` was imputed because it was in the 5% to 30% range, `embark_town` was cleaned by row removal because it was below 5%, and `deck` was removed because it was far above 30% missing.

---

## 2. Distribution and outlier checks

The EDA notebook also inspects the distribution of `age` and `fare` using histograms and boxplots. IQR-based outlier counts are computed for both variables, which helps identify unusually high or low values before modeling.

The `fare` distribution is strongly right-skewed. This is supported by the fact that the mean is substantially above the median and mode, which is a classic sign that a small number of very high ticket prices pull the mean upward. In practical terms, the dataset contains a long upper tail of high fares, while most passengers paid comparatively low fares.

---

## 3. Correlation analysis

The EDA notebook examines the correlation structure using the required six numeric feature columns:

- `survived`
- `ticket_class`
- `age`
- `siblings_spous`
- `parent_children`
- `fare`

This ensures the matrix is not computed on unrelated or redundant columns. The two strongest correlations are:

1. `ticket_class` and `fare` — this is the largest absolute off-diagonal correlation and reflects the fact that higher-class passengers paid more for their tickets.
2. `siblings_spous` and `parent_children` — this is the second strongest relationship and is consistent with family groups travelling together.

The heatmap interpretation is included in the notebook to explain these relationships in context.

---

## 4. Multivariate exploration and narrative findings

The EDA notebook includes multiple multivariate charts, each paired with a written interpretation. These include:

- survival rate by sex
- survival rate by ticket class
- survival rate by sex and ticket class heatmap
- fare distribution by survival status
- age vs. fare scatter plot colored by survival outcome
- age/fare before/after standardization check

The main story from the exploratory analysis is that survival was strongly associated with sex, class, and fare. Women had much higher survival rates than men, higher ticket classes had much better survival outcomes, and passengers in the higher-fare range were more likely to survive. The evidence suggests that wealth, cabin position, and gender-based evacuation priorities played major roles in the observed differences.

---

## 5. Modeling workflow and preprocessing discipline

The modeling notebook begins with a stratified train/test split before any preprocessing. This is important because the target variable is imbalanced and a random split could distort the distribution of the classes. Stratification keeps the same class balance in both train and test sets.

The pipeline then applies preprocessing fit only on the training split:

- numeric features: median imputation + StandardScaler
- categorical features: most-frequent imputation + OneHotEncoder

The same fitted preprocessing steps are then applied in transform-only mode to the test split. No preprocessing step is fit on the full dataset or on the test set.

---

## 6. Classification model comparison

The notebook trains three classifiers on the same train/test split:

- Logistic Regression
- Decision Tree
- Random Forest

For each classifier, it reports the full metric suite:

- confusion matrix
- accuracy
- precision
- recall
- F1 score
- ROC-AUC

The decision tree model is visualized with `plot_tree`, and the feature names and class labels are included in the generated tree.

### Observed comparison

| Model | Accuracy | Precision | Recall | F1 Score | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Random Forest | 0.8090 | 0.7429 | 0.7647 | 0.7536 | 0.8255 |
| Logistic Regression | 0.8090 | 0.7833 | 0.6912 | 0.7344 | 0.8610 |
| Decision Tree | 0.7584 | 0.6712 | 0.7206 | 0.6950 | 0.7456 |

---

## 7. Class imbalance handling and tuning

The modeling notebook compares three strategies for the imbalanced target:

- baseline / no handling
- `class_weight='balanced'`
- SMOTE applied to the training fold only

The notebook includes a written conclusion explaining the effect of the imbalance-handling strategies on the minority class. It also includes a `GridSearchCV` run on a `RandomForestClassifier(oob_score=True, ...)`, with best parameters and OOB score reported.

---

## 8. Regression side task

A secondary regression task predicts `fare` using the remaining variables as predictors. The notebook reports all four required metrics:

- MAE
- RMSE
- R²
- Adjusted R²

It also checks residuals for heteroscedasticity and interprets the pattern in the residual plot. This ensures the regression sub-task is not treated as a casual add-on but as a meaningful complementary task.

### Regression results

| Model | MAE | RMSE | R² | Adjusted R² |
|---|---:|---:|---:|---:|
| Linear Regression | 18.3920 | 41.3073 | 0.3604 | 0.2649 |

---

## 9. Final model recommendation

The final markdown summary at the end of the modeling notebook compares the classification and regression metrics as separate groups, since they are measured on different scales and should not be merged into a single metric scale.

The recommended classifier is the Random Forest. It achieves the highest F1 score among the classifiers at 0.7536, which gives the strongest precision/recall trade-off for the survival task. Its accuracy is tied with Logistic Regression at 0.8090, but its recall is higher at 0.7647, which is especially valuable when missing a positive survival case is costly. Logistic Regression has the highest ROC-AUC at 0.8610, but the Random Forest remains the better deployment choice for this class-imbalanced problem because F1 is the most relevant task-specific metric.

---

## 10. Saved pipeline artifact

The final artifact is a complete fitted pipeline saved with `joblib.dump(full_pipeline, ...)`. This includes both preprocessing steps and the final estimator, so it can be reloaded and used end-to-end on raw input data without reconstructing the pipeline manually.

The saved pipeline is designed to accept raw Titanic records, apply the exact same preprocessing logic, and generate predictions using the fitted model.
