# Keep feedback signals independent

Rank measures execution, sentiment measures direction, and lifecycle records an explicit state change. The inference policy considers these fields together per element but never collapses them into one reward score, because low-rank likes and high-rank dislikes carry opposite creative instructions that an average would destroy.
