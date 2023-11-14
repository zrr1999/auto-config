from __future__ import annotations

from typing import Any, TypeVar

import libcst as cst
from libcst import (
    Arg,
    AssignTarget,
    Call,
    ClassDef,
    FlattenSentinel,
    Index,
    Parameters,
    SimpleStatementLine,
    SimpleString,
    Subscript,
    SubscriptElement,
)
from libcst.codemod import (
    CodemodContext,
    VisitorBasedCodemodCommand,
    gather_files,
    parallel_exec_transform_with_prettyprint,
)
from libcst.codemod.visitors import AddImportsVisitor
from libcst.metadata import Scope, ScopeProvider


class ReplaceNodes(cst.CSTTransformer):
    def __init__(self, replacements: dict[cst.CSTNode, cst.CSTNode]):
        self.replacements = replacements

    def on_leave(self, original_node: cst.CSTNode, updated_node: cst.CSTNode):
        return self.replacements.get(original_node, updated_node)


def gen_type_param(
    type_param: cst.TypeVar | cst.TypeVarTuple | cst.ParamSpec, type_name: cst.Name | None = None
) -> SimpleStatementLine:
    """
    To generate the following code:
        T = TypeVar("T")
        P = ParamSpec("P")
        Ts = TypeVarTuple("Ts")
    """
    type_name = type_param.name if type_name is None else type_name
    match type_param:
        case cst.TypeVar(name, bound):
            args = [
                cst.Arg(SimpleString(f'"{type_name.value}"')),
            ]
            if bound is not None:
                args.append(Arg(bound, keyword=cst.Name("bound")))
            return SimpleStatementLine(
                [
                    cst.Assign(
                        targets=[AssignTarget(type_name)],
                        value=Call(
                            func=cst.Name("TypeVar"),
                            args=args,
                        ),
                    )
                ]
            )
        case cst.TypeVarTuple(name) | cst.ParamSpec(name):
            return SimpleStatementLine(
                [
                    cst.Assign(
                        targets=[AssignTarget(type_name)],
                        value=Call(
                            func=cst.Name(type_param.__class__.__name__),
                            args=[
                                Arg(SimpleString(f'"{type_name.value}"')),
                            ],
                        ),
                    )
                ]
            )
        case _:
            raise NotImplementedError


def __wrapper_func_remove_type_parameters():
    __remove_type_parameters_T = TypeVar("__remove_type_parameters_T", bound=cst.FunctionDef | ClassDef)

    def remove_type_parameters(
        node: __remove_type_parameters_T, prefix: str = "", suffix: str = ""
    ) -> tuple[list[SimpleStatementLine], __remove_type_parameters_T]:
        type_params = node.type_parameters
        if type_params is None:
            return [], node
        statements = []
        new_node = node.with_changes(type_parameters=None)

        slices = []
        for type_param in type_params.params:
            new_name = type_param.param.name.with_changes(value=f"{prefix}{type_param.param.name.value}{suffix}")
            statements.append(gen_type_param(type_param.param, new_name))
            slices.append(
                SubscriptElement(
                    slice=Index(value=new_name),
                ),
            )

        if isinstance(new_node, ClassDef):
            generic_base = Arg(
                value=Subscript(
                    value=cst.Name(
                        value="Generic",
                        lpar=[],
                        rpar=[],
                    ),
                    slice=slices,
                )
            )
            new_node = new_node.with_changes(bases=[*new_node.bases, generic_base])

        return statements, new_node

    return remove_type_parameters


remove_type_parameters = __wrapper_func_remove_type_parameters()


def gen_func_wrapper(node: cst.FunctionDef, type_vars: list[SimpleStatementLine]) -> cst.FunctionDef:
    wrapper = cst.FunctionDef(
        name=cst.Name(value=f"__wrapper_func_{node.name.value}"),
        params=Parameters(),
        body=cst.IndentedBlock(
            body=[
                *type_vars,
                node,
                SimpleStatementLine(
                    [
                        cst.Return(
                            value=cst.Name(
                                value=node.name.value,
                                lpar=[],
                                rpar=[],
                            )
                        ),
                    ]
                ),
            ]
        ),
    )
    return wrapper


class RemoveAnnotationCommand(VisitorBasedCodemodCommand):
    METADATA_DEPENDENCIES = (ScopeProvider,)

    def __init__(self, context: CodemodContext) -> None:
        self.node_to_wrapper: dict[cst.FunctionDef | ClassDef, Any] = {}
        super().__init__(context)

    def visit_FunctionDef(self, node: cst.FunctionDef):
        AddImportsVisitor.add_needed_import(self.context, "typing", "TypeAlias")
        AddImportsVisitor.add_needed_import(self.context, "typing", "TypeVar")
        AddImportsVisitor.add_needed_import(self.context, "typing", "ParamSpec")
        AddImportsVisitor.add_needed_import(self.context, "typing", "TypeVarTuple")

        type_params = node.type_parameters
        if type_params is None:
            return False

        type_scope = self.get_metadata(ScopeProvider, type_params)
        body_scope = self.get_metadata(ScopeProvider, node.body)
        replacemences = {}
        prefix = f"__{node.name.value}_"
        for type_param in type_params.params:
            for scope in [type_scope, body_scope]:
                assert isinstance(scope, Scope)
                for access in set(scope.accesses[type_param.param.name]):
                    assert isinstance(access.node, cst.Name)
                    replacemences[access.node] = cst.Name(value=f"{prefix}{type_param.param.name.value}")
        new_node = node.visit(ReplaceNodes(replacemences))
        assert isinstance(new_node, cst.FunctionDef)

        type_vars, new_node = remove_type_parameters(new_node, prefix=prefix)

        if type_vars:
            wrapper = gen_func_wrapper(new_node, type_vars)
            self.node_to_wrapper[node] = wrapper
        return False

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef):
        wrapper = self.node_to_wrapper.get(original_node, None)
        if wrapper is None:
            return updated_node
        func = SimpleStatementLine(
            [
                cst.Assign(
                    targets=[AssignTarget(updated_node.name)],
                    value=Call(
                        func=cst.Name(value=f"__wrapper_func_{updated_node.name.value}"),
                        args=[],
                    ),
                )
            ]
        )

        return FlattenSentinel([wrapper, func])

    def visit_ClassDef(self, node: ClassDef):
        AddImportsVisitor.add_needed_import(self.context, "typing", "Generic")
        AddImportsVisitor.add_needed_import(self.context, "typing", "TypeVar")
        AddImportsVisitor.add_needed_import(self.context, "typing", "ParamSpec")
        AddImportsVisitor.add_needed_import(self.context, "typing", "TypeVarTuple")

        type_params = node.type_parameters
        if type_params is None:
            return True

        scopes = [self.get_metadata(ScopeProvider, type_params)]
        for b in node.body.body:
            scopes.append(self.get_metadata(ScopeProvider, b))
            if isinstance(b, cst.FunctionDef):
                scopes.append(self.get_metadata(ScopeProvider, b.body))

        replacemences = {}
        prefix = f"__{node.name.value}_"
        for type_param in type_params.params:
            for scope in scopes:
                assert isinstance(scope, Scope)
                for access in set(scope.accesses[type_param.param.name]):
                    assert isinstance(access.node, cst.Name)
                    replacemences[access.node] = cst.Name(value=f"{prefix}{type_param.param.name.value}")
        new_node = node.visit(ReplaceNodes(replacemences))
        assert isinstance(new_node, ClassDef)

        type_vars, new_node = remove_type_parameters(new_node, prefix=prefix)

        if type_vars:
            self.node_to_wrapper[node] = new_node, type_vars
        return True

    def leave_ClassDef(self, original_node: ClassDef, updated_node: ClassDef):
        wrapper = self.node_to_wrapper.get(original_node, None)
        if wrapper is None:
            return updated_node
        new_node, type_vars = wrapper
        return FlattenSentinel([*type_vars, new_node])


command_instance = RemoveAnnotationCommand(CodemodContext())
files = gather_files(".")
result = parallel_exec_transform_with_prettyprint(
    command_instance,
    files,
    format_code=False,
    hide_generated=True,
    # hide_progress=True,
)
