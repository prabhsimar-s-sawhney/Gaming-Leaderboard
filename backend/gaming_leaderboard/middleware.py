"""
Middleware for timeout protection and performance monitoring.
"""
import time
import logging
from django.http import JsonResponse
from django.conf import settings
import threading

logger = logging.getLogger(__name__)


class TimeoutProtectionMiddleware:
    """Middleware to protect against long-running requests and add timeout headers."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout_threshold = getattr(settings, 'REQUEST_TIMEOUT_THRESHOLD', 30)
    
    def __call__(self, request):
        start_time = time.time()
        
        # Set a timeout for the request processing
        response = None
        request_timeout = False
        
        def process_request():
            nonlocal response
            try:
                response = self.get_response(request)
            except Exception as e:
                logger.error(f"Request processing error: {str(e)}")
                response = JsonResponse(
                    {'error': 'Internal server error'}, 
                    status=500
                )
        
        # Start request processing in a thread with timeout
        thread = threading.Thread(target=process_request)
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.timeout_threshold)
        
        if thread.is_alive():
            # Request is still running after timeout
            logger.warning(f"Request timeout for {request.path}")
            return JsonResponse(
                {'error': 'Request timeout'}, 
                status=408
            )
        
        if response is None:
            return JsonResponse(
                {'error': 'Request processing failed'}, 
                status=500
            )
        
        # Log slow requests
        duration = time.time() - start_time
        if duration > 5.0:  # Log requests taking more than 5 seconds
            logger.warning(
                f"Slow request: {request.path} took {duration:.2f} seconds"
            )
        
        # Add timing headers
        if hasattr(response, '__setitem__'):
            response['X-Response-Time'] = f"{duration:.3f}"
            response['X-Timeout-Protection'] = "enabled"
        
        return response


class WebSocketTimeoutMiddleware:
    """Middleware for WebSocket timeout protection."""
    
    def __init__(self, inner):
        self.inner = inner
    
    async def __call__(self, scope, receive, send):
        if scope['type'] == 'websocket':
            # Add timeout protection for WebSocket connections
            import asyncio
            
            async def timeout_protected_inner():
                try:
                    await asyncio.wait_for(
                        self.inner(scope, receive, send),
                        timeout=300  # 5 minutes max connection time
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"WebSocket connection timeout for {scope.get('path', 'unknown')}")
                    # Send close frame if possible
                    try:
                        await send({
                            'type': 'websocket.close',
                            'code': 4008,  # Request timeout
                        })
                    except:
                        pass
                except Exception as e:
                    logger.error(f"WebSocket error: {str(e)}")
                    try:
                        await send({
                            'type': 'websocket.close',
                            'code': 4500,  # Internal error
                        })
                    except:
                        pass
            
            await timeout_protected_inner()
        else:
            await self.inner(scope, receive, send)
