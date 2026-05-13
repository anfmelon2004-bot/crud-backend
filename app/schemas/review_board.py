from pydantic import BaseModel
from datetime import datetime
from app.models.review_board import AssignmentLevel, Semester, GradingStyle, TeamProjectLoad


class ReviewPostCreate(BaseModel):
    title: str
    content: str
    course_name: str
    professor_name: str
    assignment_level: AssignmentLevel
    team_project_load: TeamProjectLoad = TeamProjectLoad.normal
    grading_style: GradingStyle = GradingStyle.normal
    rating: int = 5
    year: int
    semester: Semester


class ReviewPostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    assignment_level: AssignmentLevel | None = None
    team_project_load: TeamProjectLoad | None = None
    grading_style: GradingStyle | None = None
    rating: int | None = None


class ReviewPostResponse(BaseModel):
    id: int
    title: str
    content: str
    course_name: str
    professor_name: str
    assignment_level: AssignmentLevel
    team_project_load: TeamProjectLoad
    grading_style: GradingStyle
    rating: int
    year: int
    semester: Semester
    author_id: int
    author_name: str
    created_at: datetime
    updated_at: datetime
    like_count: int

    model_config = {"from_attributes": True}


class ReviewPostListResponse(BaseModel):
    posts: list[ReviewPostResponse]
    total: int
    page: int
    size: int
    total_pages: int


class LikeResponse(BaseModel):
    liked: bool
    like_count: int
