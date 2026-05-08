from .schemas import DomainEntityType, DomainPredicate, PreferenceSchema


SHOPPING_PREFERENCE_SCHEMA = PreferenceSchema(
    domain_focus="shopping and product discovery preferences",
    entity_types=[
        DomainEntityType(name="Customer", description="The user/customer"),
        DomainEntityType(name="Product", description="A concrete product"),
        DomainEntityType(name="Category", description="Product category"),
        DomainEntityType(name="Brand", description="Product brand"),
        DomainEntityType(name="Feature", description="Product feature or attribute"),
        DomainEntityType(name="PriceRange", description="Budget or price preference"),
    ],
    predicates=[
        DomainPredicate(
            name="prefers",
            description="User likes or prefers something",
            allowed_object_types=["Brand", "Category", "Feature", "PriceRange"],
        ),
        DomainPredicate(
            name="dislikes",
            description="User dislikes or wants to avoid something",
            allowed_object_types=["Brand", "Category", "Feature"],
        ),
        DomainPredicate(
            name="is looking for",
            description="Current shopping intent",
            allowed_object_types=["Product", "Category", "Feature"],
        ),
        DomainPredicate(
            name="has budget of",
            description="Budget or price limit",
            allowed_object_types=["PriceRange"],
        ),
        DomainPredicate(
            name="owns",
            description="User already owns something",
            allowed_object_types=["Product", "Brand", "Category"],
        ),
        DomainPredicate(
            name="needs",
            description="Functional need or requirement",
            allowed_object_types=["Feature", "Category"],
        ),
        DomainPredicate(
            name="is interested in",
            description="Weak interest signal",
            allowed_object_types=["Brand", "Category", "Feature", "Product"],
        ),
    ],
)
