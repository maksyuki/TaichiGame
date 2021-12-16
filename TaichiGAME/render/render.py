from typing import Callable, List, Optional, Tuple, cast
import numpy as np

import taichi as ti
try:
    from taichi.ui.gui import GUI
except ImportError:
    from taichi.misc.gui import GUI

from ..math.matrix import Matrix
from ..geometry.shape import Capsule, Circle, Edge
from ..geometry.shape import Polygon, Shape, ShapePrimitive
from ..dynamics.joint.joint import Joint
from ..common.config import Config


class Render():
    @staticmethod
    def rd_point(gui: GUI,
                 point: Matrix,
                 color: int = ti.rgb_to_hex([1.0, 1.0, 1.0]),
                 radius: float = 2.0) -> None:
        assert gui is not None
        assert 0 <= point.x <= 1.0
        assert 0 <= point.y <= 1.0
        gui.circle([point.x, point.y], color, radius)

    @staticmethod
    def rd_points(gui: GUI,
                  points: List[Matrix],
                  color: int = ti.rgb_to_hex([1.0, 1.0, 1.0]),
                  radius: float = 2.0) -> None:
        assert gui is not None

        for p in points:
            Render.rd_point(gui, p, color, radius)

    @staticmethod
    def rd_line(gui: GUI,
                p1: Matrix,
                p2: Matrix,
                color: int = ti.rgb_to_hex([1.0, 1.0, 1.0]),
                radius: float = 1.0) -> None:
        assert gui is not None
        assert 0 <= p1.x <= 1.0
        assert 0 <= p1.y <= 1.0
        assert 0 <= p2.x <= 1.0
        assert 0 <= p2.y <= 1.0

        gui.line([p1.x, p1.y], [p2.x, p2.y], radius, color)

    @staticmethod
    def rd_lines(gui: GUI,
                 lines: List[Tuple[Matrix, Matrix]],
                 color: int = ti.rgb_to_hex([1.0, 1.0, 1.0]),
                 radius: float = 1.0) -> None:
        assert gui is not None

        for lin in lines:
            Render.rd_line(gui, lin[0], lin[1], color, radius)

    @staticmethod
    def rd_shape(
        gui: GUI,
        prim: ShapePrimitive,
        world_to_screen: Callable[[Matrix], Matrix],
        meter_to_pixel: float,
        color: int = ti.rgb_to_hex([1.0, 1.0, 1.0])
    ) -> None:
        assert gui is not None
        assert prim._shape is not None

        if prim._shape.type == Shape.Type.Polygon:
            Render.rd_polygon(gui, prim, world_to_screen)

        elif prim._shape.type == Shape.Type.Ellipse:
            Render.rd_ellipse()

        elif prim._shape.type == Shape.Type.Circle:
            Render.rd_circle(gui, prim, world_to_screen, meter_to_pixel, color)

        elif prim._shape.type == Shape.Type.Curve:
            Render.rd_curve()

        elif prim._shape.type == Shape.Type.Edge:
            Render.rd_edge(gui, prim, world_to_screen)

        elif prim._shape.type == Shape.Type.Capsule:
            Render.rd_capsule(gui, prim, world_to_screen, meter_to_pixel,
                              color)

        elif prim._shape.type == Shape.Type.Sector:
            raise NotImplementedError

    @staticmethod
    def rd_polygon(gui: GUI, prim: ShapePrimitive,
                   world_to_screen: Callable[[Matrix], Matrix]) -> None:

        # [trick] draw polygon by draw multi triangle
        poly: Polygon = cast(Polygon, prim._shape)
        assert len(poly.vertices) >= 3

        outer_line_st: Optional[np.ndarray] = None
        outer_line_ed: Optional[np.ndarray] = None
        fill_tri_pa: Optional[np.ndarray] = None
        fill_tri_pb: Optional[np.ndarray] = None
        fill_tri_pc: Optional[np.ndarray] = None

        is_first: bool = True

        # NOTE: the vertices can form a close shape,
        # so the first vertex and last vertex are same
        # print('render poly')
        vert_len: int = len(poly.vertices)
        for i in range(vert_len - 1):
            wordpa: Matrix = Matrix.rotate_mat(
                prim._rot) * poly.vertices[i] + prim._xform
            scrnpa: Matrix = world_to_screen(wordpa)

            wordpb: Matrix = Matrix.rotate_mat(
                prim._rot) * poly.vertices[i + 1] + prim._xform
            scrnpb: Matrix = world_to_screen(wordpb)

            if is_first:
                is_first = False
                outer_line_st = np.array([[scrnpa.x, scrnpa.y]])
                outer_line_ed = np.array([[scrnpb.x, scrnpb.y]])
            else:
                tmpa = np.array([[scrnpa.x, scrnpa.y]])
                tmpb = np.array([[scrnpb.x, scrnpb.y]])
                outer_line_st = np.concatenate((outer_line_st, tmpa))
                outer_line_ed = np.concatenate((outer_line_ed, tmpb))

        assert outer_line_st is not None
        assert outer_line_ed is not None

        fill_tri_pa = np.repeat(np.array([outer_line_st[0]]),
                                vert_len - 3,
                                axis=0)
        fill_tri_pb = outer_line_st[1:-1]
        fill_tri_pc = outer_line_st[2:]

        # print('poly ver:')
        # for v in poly.vertices:
        # print(v)
        # print('end')
        # print(f'line_len: {len(outer_line_st)}')
        # for v in outer_line_st:
        # print(v)

        gui.lines(outer_line_st,
                  outer_line_ed,
                  radius=2.0,
                  color=Config.OuterLineColor)
        gui.triangles(fill_tri_pa,
                      fill_tri_pb,
                      fill_tri_pc,
                      color=Config.FillColor)

    @staticmethod
    def rd_ellipse() -> None:
        raise NotImplementedError

    @staticmethod
    def rd_circle(
        gui: GUI,
        prim: ShapePrimitive,
        world_to_screen: Callable[[Matrix], Matrix],
        meter_to_pixel: float,
        color: int = ti.rgb_to_hex([1.0, 1.0, 1.0])
    ) -> None:
        cir: Circle = cast(Circle, prim._shape)
        scrnp: Matrix = world_to_screen(prim._xform)
        gui.circle([scrnp.x, scrnp.y],
                   color,
                   radius=cir.radius * meter_to_pixel)

    @staticmethod
    def rd_curve() -> None:
        raise NotImplementedError

    @staticmethod
    def rd_edge(gui: GUI, prim: ShapePrimitive,
                world_to_screen: Callable[[Matrix], Matrix]) -> None:
        edg: Edge = cast(Edge, prim._shape)
        tmp1: Matrix = world_to_screen(edg.start + prim._xform)
        tmp2: Matrix = world_to_screen(edg.end + prim._xform)
        Render.rd_point(gui, tmp1, Config.AxisPointColor)
        Render.rd_point(gui, tmp2, Config.AxisPointColor)
        Render.rd_line(gui, tmp1, tmp2, Config.AxisLineColor)

        center: Matrix = edg.center()
        center += prim._xform
        Render.rd_line(gui, world_to_screen(center),
                       world_to_screen(center + edg.normal * 0.1),
                       Config.AxisLineColor)

    @staticmethod
    def rd_capsule(
        gui: GUI,
        prim: ShapePrimitive,
        world_to_screen: Callable[[Matrix], Matrix],
        meter_to_pixel: float,
        color: int = ti.rgb_to_hex([1.0, 1.0, 1.0])
    ) -> None:
        cap: Capsule = cast(Capsule, prim._shape)

        # Render.rd_polygon(gui, prim, world_to_screen)
        offset: float = np.fmin(cap.width, cap.height) / 2.0
        tmp1: Matrix = Matrix([0.0, 0.0], 'vec')
        tmp2: Matrix = Matrix([0.0, 0.0], 'vec')
        if cap.width > cap.height:
            tmp1.x = prim._xform.x - offset
            tmp1.y = prim._xform.y
            tmp2.x = prim._xform.x + offset
            tmp2.y = prim._xform.y
        else:
            tmp1.x = prim._xform.x
            tmp1.y = prim._xform.y - offset
            tmp2.x = prim._xform.x
            tmp2.y = prim._xform.y + offset

        tmp1 = world_to_screen(tmp1)
        tmp2 = world_to_screen(tmp2)
        gui.circle([tmp1.x, tmp1.y], color, radius=offset * meter_to_pixel)
        gui.circle([tmp2.x, tmp2.y], color, radius=offset * meter_to_pixel)

    @staticmethod
    def rd_rect(gui: GUI,
                p1: Matrix,
                p2: Matrix,
                color: int = ti.rgb_to_hex([1.0, 1.0, 1.0]),
                radius: float = 1.0) -> None:
        assert gui is not None
        assert 0 <= p1.x <= 1.0
        assert 0 <= p1.y <= 1.0
        assert 0 <= p2.x <= 1.0
        assert 0 <= p2.y <= 1.0

        gui.rect([p1.x, p1.y], [p2.x, p2.y], radius, color)

    @staticmethod
    def rd_joint(gui, joint: Joint) -> None:
        raise NotImplementedError

    @staticmethod
    def rd_angle_line(gui: GUI, prim: ShapePrimitive,
                      world_to_screen: Callable[[Matrix], Matrix]) -> None:
        xpos: Matrix = Matrix([0.3, 0.0], 'vec')
        ypos: Matrix = Matrix([0.0, 0.3], 'vec')

        assert prim._shape is not None
        mc: Matrix = Matrix.rotate_mat(prim._rot) * prim._shape.center()
        start: Matrix = prim._xform + mc
        xpos = Matrix.rotate_mat(prim._rot) * xpos + start
        ypos = Matrix.rotate_mat(prim._rot) * ypos + start

        Render.rd_line(gui, world_to_screen(start), world_to_screen(xpos),
                       Config.AngleLineXColor)
        Render.rd_line(gui, world_to_screen(start), world_to_screen(ypos),
                       Config.AngleLineYColor)
