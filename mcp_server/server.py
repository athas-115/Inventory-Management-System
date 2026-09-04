import json
import os
from typing import Optional

import httpx
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

load_dotenv()

API_URL = os.getenv("INVENTORY_API_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.getenv("INVENTORY_API_KEY", "")

server = MCPServer("Inventory Management")


def get_headers():
    headers = {
        "Content-Type": "application/json",
    }

    if API_KEY:
        headers["x-agent-secret"] = API_KEY

    return headers


async def make_request(
    method: str,
    endpoint: str,
    *,
    params=None,
    json_data=None,
):
    url = f"{API_URL}{endpoint}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(
            method,
            url,
            params=params,
            json=json_data,
            headers=get_headers(),
        )

        if response.is_error:
            try:
                error_data = response.json()
            except ValueError:
                error_data = response.text

            return {
                "error": True,
                "status_code": response.status_code,
                "message": error_data,
            }

        if not response.content:
            return {}

        return response.json()

async def get_or_create_product(name: str):
    products = await make_request("GET", "/api/products")

    for product in products:
        if product["name"].lower() == name.lower():
            return product

    return await make_request(
        "POST",
        "/api/products",
        json_data={"name": name},
    )


async def get_or_create_location(name: str):
    locations = await make_request("GET", "/api/locations")

    for location in locations:
        if location["name"].lower() == name.lower():
            return location

    return await make_request(
        "POST",
        "/api/locations",
        json_data={"name": name},
    )


async def find_batch_for_product(
    product_id: int,
    location_id: Optional[int] = None,
):
    params = {
        "product_id": product_id,
        "include_depleted": False,
    }

    if location_id is not None:
        params["location_id"] = location_id

    batches = await make_request(
        "GET",
        "/api/inventory",
        params=params,
    )

    batches = [
        batch
        for batch in batches
        if batch.get("quantity", 0) > 0
    ]

    batches.sort(
        key=lambda batch: (
            0 if batch.get("status") == "ACTIVE" else 1,
            batch.get("expiry_date") or "9999-12-31",
        )
    )

    return batches


@server.tool()
async def add_inventory(
    product_name: str,
    location_name: str,
    quantity: int,
    expiry_date: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """
    Add inventory for a product at a location.
    """

    product = await get_or_create_product(product_name)
    location = await get_or_create_location(location_name)

    payload = {
        "product_id": product["id"],
        "location_id": location["id"],
        "quantity": quantity,
    }

    if expiry_date:
        payload["expiry_date"] = expiry_date

    if notes:
        payload["notes"] = notes

    result = await make_request(
        "POST",
        "/api/inventory",
        json_data=payload,
    )

    return json.dumps(result, default=str)


@server.tool()
async def consume_item(
    product_name: str,
    quantity: int,
    location_name: Optional[str] = None,
    action: str = "DEPLETE",
) -> str:
    """
    Consume inventory for a product.
    """

    product = await get_or_create_product(product_name)

    location_id = None

    if location_name:
        location = await get_or_create_location(location_name)
        location_id = location["id"]

    batches = await find_batch_for_product(
        product["id"],
        location_id,
    )

    if not batches:
        return json.dumps({
            "error": f"No available inventory found for '{product_name}'."
        })

    batch = batches[0]

    quantity_to_consume = min(
        quantity,
        batch["quantity"],
    )

    payload = {
        "batch_id": batch["id"],
        "quantity": quantity_to_consume,
        "action": action,
    }

    result = await make_request(
        "POST",
        "/api/inventory/consume",
        json_data=payload,
    )

    return json.dumps(result, default=str)


@server.tool()
async def move_item(
    product_name: str,
    source_location: str,
    target_location: str,
    quantity: Optional[int] = None,
) -> str:
    """
    Move inventory from one location to another.
    """

    source = await get_or_create_location(source_location)
    target = await get_or_create_location(target_location)
    product = await get_or_create_product(product_name)

    batches = await find_batch_for_product(
        product["id"],
        source["id"],
    )

    if not batches:
        return json.dumps({
            "error": (
                f"No available inventory for '{product_name}' "
                f"at '{source_location}'."
            )
        })

    batch = batches[0]

    move_quantity = quantity or batch["quantity"]
    move_quantity = min(
        move_quantity,
        batch["quantity"],
    )

    payload = {
        "batch_id": batch["id"],
        "to_location_id": target["id"],
        "quantity": move_quantity,
    }

    result = await make_request(
        "POST",
        "/api/inventory/move",
        json_data=payload,
    )

    return json.dumps(result, default=str)


@server.tool()
async def get_stock_report(
    report_type: str = "stock",
    days: int = 30,
) -> str:
    """
    Get inventory reports.
    
    report_type can be stock, low-stock, or expiring.
    """

    if report_type == "low-stock":
        result = await make_request(
            "GET",
            "/api/reports/low-stock",
        )

    elif report_type == "expiring":
        result = await make_request(
            "GET",
            "/api/reports/expiring",
            params={"days": days},
        )

    else:
        result = await make_request(
            "GET",
            "/api/reports/stock",
        )

    return json.dumps(result, default=str)


@server.tool()
async def list_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
) -> str:
    """
    List products in the inventory system.
    """

    params = {}

    if search:
        params["search"] = search

    if category:
        params["category"] = category

    result = await make_request(
        "GET",
        "/api/products",
        params=params,
    )

    return json.dumps(result, default=str)


@server.tool()
async def list_locations() -> str:
    """
    List all inventory locations.
    """

    result = await make_request(
        "GET",
        "/api/locations",
    )

    return json.dumps(result, default=str)


if __name__ == "__main__":
    server.run()