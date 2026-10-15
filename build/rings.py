"""Write funding rings into the graph: WCC over FUNDED + CREATED (Wallet and Coin only, so hubs never
join two groups), then one :Ring per component with 2+ creators, and (:Wallet)-[:IN_RING]->(:Ring).

    FALKORDB_PORT=16379 python -m build.rings
"""
import time

from app.graph import graph

WCC = """CALL algo.WCC({nodeLabels:['Wallet','Coin'], relationshipTypes:['FUNDED','CREATED']}) YIELD node, componentId"""


def main() -> None:
    g = graph()
    g.query("MATCH (r:Ring) DETACH DELETE r", timeout=15000)
    t = time.time()
    res = g.query(WCC + """
        WITH componentId,
             collect(CASE WHEN node:Wallet AND node.launches > 0 THEN node END) AS creators,
             sum(CASE WHEN node:Coin THEN 1 ELSE 0 END) AS coins,
             sum(CASE WHEN node:Coin AND node.graduated THEN 1 ELSE 0 END) AS grads,
             sum(CASE WHEN node:Wallet AND node.launches = 0 THEN 1 ELSE 0 END) AS funders
        WHERE size(creators) >= 2
        CREATE (r:Ring {rid: componentId, creators: size(creators), coins: coins, graduations: grads,
                        funders: funders, grad_rate: CASE WHEN coins > 0 THEN toFloat(grads) / coins ELSE 0.0 END})
        WITH r, creators UNWIND creators AS w
        CREATE (w)-[:IN_RING]->(r)
    """, timeout=15000)
    print("rings written:", res.nodes_created, "nodes,", res.relationships_created, "edges in", round(time.time() - t, 1), "s")


if __name__ == "__main__":
    main()
