

class StackAccessor(object):
    def __init__(self, scope, id, **kwargs):
        self._accessor = {}
        self.scope = scope
        self.id = id
        self.options = {**kwargs}

    def delete(self, collection_id):
        del self._accessor[collection_id]
        return True

    def get(self, collection_id):
        return self._accessor.get(collection_id, None)

    def __getattr__(self, attr):
        if not getattr(self, attr):
            return self._accessor.get(attr, None)
        else:
            return getattr(self, attr)

    def new(self, collection_id):
        self._accessor[collection_id] = ConstructCollection(
            scope=self.scope,
            id=collection_id,
            parent=self
            )
        return self._accessor[collection_id]

    def put(self, collection_id, collection):
        try:
            self._accessor[collection_id] = collection
            return True

        except Exception:
            return False

    def set(self, **kwargs):
        self.options = {**self.options, **kwargs}


class ConstructCollection(StackAccessor):
    def __init__(self, scope, id, **kwargs):
        super().__init__(self, scope, id, **kwargs)
        self.parent = kwargs.get('parent', None)
        self.scope = self.parent.scope
        self.base_construct = self.options.get('base_construct', None)

    def assign_construct(self, construct):
        self.base_construct = construct

    def new(self, id, base_construct=None, **kwargs):
        base_construct = self.base_construct if not base_construct else base_construct
        self._accesor[id] = StackConstruct(
            scope=self.scope,
            id=id,
            base_construct=base_construct,
            **kwargs
        )


class StackConstruct(ConstructCollection):
    def __init__(self, scope, id, **kwargs):
        super().__init__(self, scope, id, **kwargs)
        self.construct = None
        self.params = {}
        self._protected_keys = ['scope', 'id']
        self._required_args = []

        if self._required_args:
            self._check_requirements(kwargs)

    def add_option(self, **kwargs):
        for arg in kwargs:
            if arg not in self._protected_keys:
                self.options[arg] = kwargs[arg]
            elif arg == 'scope':
                self.scope = kwargs[arg]
            elif arg == 'id':
                self.id = kwargs[arg]
            raise ValueError(f'unable to process StackConstruct.add_option - {arg} for construct {self.id}')

    def build(self):
        self._construct_params()
        self.construct = self.base_construct(
            scope=self.scope,
            id=self.id,
            **self.params
        )

    def __getattr__(self, attr):
        if not getattr(self, attr):
            return self.options.get(attr, None)
        else:
            return getattr(self, attr)

    def new(self, id, base_construct=None, **kwargs):
        base_construct = self.base_construct if not base_construct else base_construct
        self.construct = base_construct(
            scope=self.scope,
            id=self.id,
            **kwargs
        )

    def _check_requirements(self, kwargs):
        for required in self._required_args:
            if required not in kwargs.keys():
                error_message = "".join([
                    f"StackConstruct of type {self.id} has the following ",
                    f"required arguments: {self._required_args}",
                ])
                raise ValueError(error_message)

    def _construct_params(self):
        for key, value in self.options:
            if getattr(self, key, None):
                self.params[key] = getattr(self, key)(value)
            else:
                self.params[key] = value