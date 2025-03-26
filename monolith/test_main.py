import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from main import fetch_page_source, generate_test_plan, execute_test_plan, ExecutionError

@pytest.mark.asyncio
async def test_fetch_page_source():
    # Mock the HTTP client
    mock_client = AsyncMock(httpx.AsyncClient)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html>Mock Page Source</html>"
    mock_client.post.return_value = mock_response

    # Call the function
    result = await fetch_page_source(mock_client, "http://mock-playwright", "http://example.com", MagicMock())

    # Assertions
    assert result == "<html>Mock Page Source</html>"
    mock_client.post.assert_called_once_with("http://mock-playwright/navigate", json={"url": "http://example.com"})

@pytest.mark.asyncio
async def test_fetch_page_source_failure():
    # Mock the HTTP client
    mock_client = AsyncMock(httpx.AsyncClient)
    mock_client.post.side_effect = httpx.RequestError("Network error")

    # Call the function and expect an exception
    with pytest.raises(ExecutionError, match="Failed to fetch page source: Network error"):
        await fetch_page_source(mock_client, "http://mock-playwright", "http://example.com", MagicMock())

@pytest.mark.asyncio
async def test_generate_test_plan():
    # Mock the LLM
    mock_llm = MagicMock()
    mock_llm.generate_str = AsyncMock(return_value='{"url": "http://example.com", "test_plan": {"description": "Test", "steps": []}}')

    # Call the function
    result = await generate_test_plan(mock_llm, "http://example.com", "<html>Mock Page Source</html>", "Test description", MagicMock())

    # Assertions
    assert result == {"url": "http://example.com", "test_plan": {"description": "Test", "steps": []}}
    mock_llm.generate_str.assert_called_once()

@pytest.mark.asyncio
async def test_generate_test_plan_invalid_json():
    # Mock the LLM
    mock_llm = MagicMock()
    mock_llm.generate_str = AsyncMock(return_value="Invalid JSON")

    # Call the function and expect an exception
    with pytest.raises(ExecutionError, match="Failed to decode JSON from LLM response"):
        await generate_test_plan(mock_llm, "http://example.com", "<html>Mock Page Source</html>", "Test description", MagicMock())

@pytest.mark.asyncio
async def test_execute_test_plan():
    # Mock the HTTP client
    mock_client = AsyncMock(httpx.AsyncClient)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "success"}
    mock_client.post.return_value = mock_response

    # Call the function
    result = await execute_test_plan(mock_client, "http://mock-playwright", {"test_plan": {}}, 1, 300, MagicMock())

    # Assertions
    assert result == {"result": "success"}
    mock_client.post.assert_called_once_with(
        "http://mock-playwright/execute", json={"test_plan": {}}, timeout=300
    )

@pytest.mark.asyncio
async def test_execute_test_plan_retry():
    # Mock the HTTP client
    mock_client = AsyncMock(httpx.AsyncClient)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "success"}

    # Simulate a timeout on the first call and success on the second
    mock_client.post.side_effect = [httpx.TimeoutException("Timeout"), mock_response]

    # Call the function
    result = await execute_test_plan(mock_client, "http://mock-playwright", {"test_plan": {}}, 2, 300, MagicMock())

    # Assertions
    assert result == {"result": "success"}
    assert mock_client.post.call_count == 2

@pytest.mark.asyncio
async def test_execute_test_plan_failure():
    # Mock the HTTP client
    mock_client = AsyncMock(httpx.AsyncClient)
    mock_client.post.side_effect = httpx.HTTPStatusError("Error", request=None, response=MagicMock(status_code=500))

    # Call the function and expect an exception
    with pytest.raises(ExecutionError, match="Failed after 1 retries: Error"):
        await execute_test_plan(mock_client, "http://mock-playwright", {"test_plan": {}}, 1, 300, MagicMock())