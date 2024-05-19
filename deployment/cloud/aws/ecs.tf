resource "aws_ecs_cluster" "botfarm" {
  name = var.ecs_cluster
}

resource aws_ecs_service "amibot" {
  name = var.ecs_service
  desired_count = var.scale_min

  ecs_cluster = aws_ecs_cluster.botfarm.id
  task_definition = aws_ecs_task_definition.tsk_amibot.arn

}

resource aws_ecs_task_definition "tsk_amibot" {
  name = "task.${var.project_name}.${var.env}"
  family = "task.${var.project_name}.${var.env}"

  cpu = var.specs_cpu
  memory = var.specs_ram

  requires_compatibilities = ["FARGATE"]
  execution_role_arn = aws_iam_role.container_role.arn
  container_definitions = jsonencode(
    {
      "entryPoint": ["/"]
    }
  )
  image = "${var.image}:${var.image_version}"


}

