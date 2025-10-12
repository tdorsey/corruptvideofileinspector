"""GraphQL schema definition."""

import strawberry

from src.api.graphql.resolvers import Mutation, Query

# Create the GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
