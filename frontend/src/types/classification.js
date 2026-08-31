/**
 * Shapes returned by the backend classification API.
 *
 * The project is JavaScript, not TypeScript, so these are JSDoc typedefs:
 * they give editors real autocomplete and catch typos against the actual API
 * contract without converting the codebase to TypeScript for one feature.
 *
 * Mirrors `backend/app/schemas/classification.py`.
 */

/**
 * @typedef {Object} RolePrediction
 * @property {string} role        Category label, e.g. "DATA-ENGINEER".
 * @property {number} confidence  Relative score in [0, 1]. Scores across all
 *                                classes sum to 1, but they are NOT calibrated
 *                                probabilities — use them to rank only.
 */

/**
 * @typedef {Object} ClassificationResponse
 * @property {string} resume_id
 * @property {string} predicted_role              Highest-confidence role.
 * @property {number} confidence                  Confidence in predicted_role.
 * @property {RolePrediction[]} top_predictions   Sorted by descending confidence.
 * @property {string} classifier_version          Model name and training date.
 */

export {};
