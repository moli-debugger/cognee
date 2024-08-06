from sqlalchemy import func, select
from sqlalchemy.orm import aliased
from cognee.infrastructure.databases.relational import get_relational_engine
from ..models import PipelineRun

async def get_pipeline_status(pipeline_names: [str]):
    db_engine = get_relational_engine()

    async with db_engine.get_async_session() as session:
        query = select(
            PipelineRun,
            func.row_number().over(
                partition_by = PipelineRun.run_name,
                order_by = PipelineRun.created_at.desc(),
            ).label("rn")
        ).filter(PipelineRun.run_name.in_(pipeline_names)).subquery()

        aliased_pipeline_run = aliased(PipelineRun, query)

        latest_runs = (
            select(aliased_pipeline_run).filter(query.c.rn == 1)
        )
      
        runs = (await session.execute(latest_runs)).scalars().all()

        pipeline_statuses = {
            run.run_name: run.status for run in runs
        }

        return pipeline_statuses

        # f"""SELECT data_id, status
        # FROM (
        #     SELECT data_id, status, ROW_NUMBER() OVER (PARTITION BY data_id ORDER BY created_at DESC) as rn
        #     FROM cognee.cognee.task_runs
        #     WHERE data_id IN ({formatted_data_ids})
        # ) t
        # WHERE rn = 1;"""

      # return { dataset["data_id"]: dataset["status"] for dataset in datasets_statuses }
