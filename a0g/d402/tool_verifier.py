"""
0G-based tool verification and rating system
"""
import functools
import time
import json
from typing import Dict, Any, Callable, Optional

from openai import OpenAI
from .ratings import BaseRatings


class LLMToolVerifier:

    """Tool verifier for rating calculation"""

    def __init__(self, ratings: BaseRatings,
                 client: Optional[OpenAI] = None,
                 model: str = "gpt-4.1-mini"):
        self.ratings = ratings
        self.client = client
        self.model = model

    def track_usage(self, resource: str,
                    inputs: Dict[str, Any],
                    outputs: Dict[str, Any],
                    description: str,
                    success: bool = True,
                    execution_time: float = 0.0):
        """Tracks tool usage with 0G verification"""
        # Track basic metrics locally
        self.ratings.inc(f"{resource}:total_calls")

        if success:
            self.ratings.inc(f"{resource}:success_calls")
            # Only send for verification if call was successful
            if self.client is not None:
                try:
                    rating = self._verify_with_0g(resource,
                                                  inputs, outputs,
                                                  description,
                                                  execution_time)
                    if rating is not None:
                        for rating_key in ["correctness_score",
                                           "performance_score",
                                           "reliability_score",
                                           "usability_score"]:
                            self.ratings.inc(f"{resource}:{rating_key}",
                                             amount=rating[rating_key])
                except Exception as e:
                    print(f"⚠️ LLM verification failed for {resource}: {e}")
        else:
            self.ratings.inc(f"{resource}:failed_calls")

        # Store execution time
        self.ratings.inc(f"{resource}:total_time",
                         amount=execution_time)

    def _verify_with_0g(self, resource: str, inputs: Dict[str, Any], outputs: Dict[str, Any],
                       description: str, execution_time: float) -> Optional[Dict[str, Any]]:
        """Verify tool performance using LLM"""
        if not self.client:
            return None

        try:

            # Prepare verification prompt
            verification_prompt = self._create_verification_prompt(
                resource, inputs, outputs, description, execution_time
            )

            # Request structured output from 0G
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a tool performance evaluator. Analyze the provided tool execution and return a structured rating."},
                    {"role": "user", "content": verification_prompt}
                ],
                response_format={
                    "type": "json_object",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "correctness_score": {"type": "number", "minimum": 0, "maximum": 10},
                            "performance_score": {"type": "number", "minimum": 0, "maximum": 10},
                            "reliability_score": {"type": "number", "minimum": 0, "maximum": 10},
                            "usability_score": {"type": "number", "minimum": 0, "maximum": 10},
                        },
                        "required": ["overall_rating", "correctness_score", "performance_score",
                                     "reliability_score", "usability_score", "reasoning", "verified"]
                    }
                }
            )

            # Parse response
            rating_data = json.loads(response.choices[0].message.content)
            print(rating_data)
            return rating_data

        except Exception as e:
            print(f"❌ LLM verification error: {e}")
            return None

    def _create_verification_prompt(self, resource: str, inputs: Dict[str, Any],
                                  outputs: Dict[str, Any], description: str, execution_time: float) -> str:
        """Create prompt for 0G verification"""
        return f"""
Please evaluate the following tool execution and provide a structured rating:

**Tool Information:**
- Name: {resource}
- Description: {description}
- Execution Time: {execution_time:.3f} seconds

**Inputs:**
{json.dumps(inputs, indent=2, ensure_ascii=False)}

**Outputs:**
{json.dumps(outputs, indent=2, ensure_ascii=False)}

**Evaluation Criteria:**
1. **Correctness Score (0-10)**: How accurate and correct are the outputs given the inputs?
2. **Performance Score (0-10)**: How well does the execution time compare to expected performance?
3. **Reliability Score (0-10)**: How consistent and reliable does this tool appear?
4. **Usability Score (0-10)**: How user-friendly and well-structured are the inputs/outputs?

**Required Response Format:**
Return a JSON object with:
- correctness_score: Score 0-10 for correctness
- performance_score: Score 0-10 for performance
- reliability_score: Score 0-10 for reliability
- usability_score: Score 0-10 for usability

Focus on objective evaluation based on the data provided.
"""

    def get_tool_stats(self, resource: str) -> Dict[str, Any]:
        """Gets comprehensive statistics including 0G ratings"""
        total_calls = self.ratings.get(f"{resource}:total_calls")
        success_calls = self.ratings.get(f"{resource}:success_calls")
        failed_calls = self.ratings.get(f"{resource}:failed_calls")
        total_time = self.ratings.get(f"{resource}:total_time")
        correctness_score = self.ratings.get(f"{resource}:correctness_score")
        performance_score = self.ratings.get(f"{resource}:performance_score")
        reliability_score = self.ratings.get(f"{resource}:reliability_score")
        usability_score = self.ratings.get(f"{resource}:usability_score")

        success_rate = (success_calls / total_calls * 100) if total_calls > 0 else 0
        avg_time = (total_time / total_calls) if total_calls > 0 else 0

        correctness_score = (correctness_score / total_calls) if total_calls > 0 else 0
        performance_score = (performance_score / total_calls) if total_calls > 0 else 0
        reliability_score = (reliability_score / total_calls) if total_calls > 0 else 0
        usability_score = (usability_score / total_calls) if total_calls > 0 else 0

        return {
            "total_calls": total_calls,
            "success_calls": success_calls,
            "failed_calls": failed_calls,

            "success_rate": round(success_rate, 2),

            "avg_execution_time": round(avg_time, 2),

            "correctness_score": round(correctness_score, 2),
            "performance_score": round(performance_score, 2),
            "reliability_score": round(reliability_score, 2),
            "usability_score": round(usability_score, 2),
        }


def d402(ratings: BaseRatings,
         client: Optional[OpenAI] = None,
         model: str = "gpt-4.1-mini",
         resource: Optional[str] = None):
    """
    Decorator for automatic tool rating with LLM verification
    """

    _llm_verifier = LLMToolVerifier(ratings,
                                    client=client,
                                    model=model)

    def decorator(func: Callable) -> Callable:
        nonlocal resource

        if resource is None:
            resource = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            result = None
            inputs = None
            outputs = None

            try:
                # Capture inputs (simplified - in production, use proper serialization)
                inputs = {
                    "args": [str(arg) for arg in args],  # Convert to strings for JSON serialization
                    "kwargs": {k: str(v) for k, v in kwargs.items()}
                }

                result = func(*args, **kwargs)

                # Capture outputs
                outputs = {
                    "result": str(result) if result is not None else None,
                    "type": str(type(result).__name__),
                    "success": True
                }

                return result
            except Exception as e:
                success = False
                outputs = {
                    "error": str(e),
                    "type": "error",
                    "success": False
                }
                raise e
            finally:
                execution_time = time.time() - start_time
                _llm_verifier.track_usage(
                    resource, inputs or {}, outputs or {},
                    func.__doc__, success, execution_time
                )
                tool_stats = _llm_verifier.get_tool_stats(resource)
                description = func.__doc__ + "\n" + "\n".join([f"{k.capitalize()}: {v}" for k, v in tool_stats.items()])
                wrapper.__doc__ = description

        tool_stats = _llm_verifier.get_tool_stats(resource)
        description = func.__doc__ + "\n" + "\n".join([f"{k.capitalize()}: {v}" for k, v in tool_stats.items()])
        wrapper.__doc__ = description

        return wrapper

    return decorator
