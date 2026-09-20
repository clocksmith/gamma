import torch

from pysrc.model import Transformer, TransformerConfig, MatmulQuantization
from pysrc.quantization import Quantization
from pysrc.data import CollatedArticlesDataLoader
from pysrc.save_outputs import save_transformer_outputs_for_article_subset


def main() -> None:
    device = torch.device("cuda")
    max_article_tokens: int | None = 2**17
    micro_batch_tokens: int = max_article_tokens

    quantization_block_size: int | None = None

    weight_quantization = Quantization(
        buckets=15,
        block_size=quantization_block_size,
        scale_dtype=torch.bfloat16,
        arithmetic_dtype=torch.float32,
        scale_init="scaled_max",
        epsilon=None,
    )
    activation_quantization = Quantization(
        buckets=256,
        block_size=quantization_block_size,
        scale_dtype=torch.bfloat16,
        arithmetic_dtype=torch.float32,
        scale_init="scaled_mean",
        epsilon=None,
    )
    matmul_quantization = MatmulQuantization(
        weight=weight_quantization, activation=activation_quantization
    )

    model: Transformer = Transformer(
        TransformerConfig(
            vocabulary_size=205,
            prior_embedding=True,
            prior_logit_mixing=False,
            max_variable_sequence_length=None,
            n_layers=12,
            attention_weight_sharing_pattern=list(range(12)),
            mlp_weight_sharing_pattern=list(range(12)),
            d_model=192,
            kimi_linear=[True, True, True, False] * 3,
            window_size=1024,
            window_size_multipliers=None,
            n_query_heads=3,
            n_key_value_heads=3,
            d_head=64,
            d_mla=None,
            rope_base=10_000,
            half_truncate_rope=False,
            query_key_norm=True,
            query_key_norm_gain=False,
            kimi_linear_d_head=64,
            kimi_linear_n_heads=3,
            kimi_linear_convolution_size=4,
            value_embedding_pattern=None,
            prior_value_embedding=False,
            attention_scale=None,
            d_mlp=768,
            activation_function="relu_squared",
            embedding_norm=True,
            prior_embedding_norm=True,
            skip_connections=True,
            token_embedding_connections=True,
            prior_embedding_connections=False,
            dropout=0.0,
            logit_softcap=15.0,
            prior_logprob_cap=-12.0,
            prior_embedding_on_logprobs=False,
            gradient_checkpointing=False,
            embedding_init="normal",
            prior_embedding_init="normal",
            up_init="kaiming_uniform",
            down_init="kaiming_uniform",
            unembedding_init="kaiming_uniform",
            convolution_init="kaiming_uniform",
            logit_mixing_head_init="zero",
            activation_dtype=torch.float32,
            attention_dtype=torch.float32,
            logit_dtype=torch.float32,
            weight_dtype=torch.float32,
            mlp_quantization=matmul_quantization,
            attention_full_rank_quantization=matmul_quantization,
            attention_low_rank_quantization=matmul_quantization,
            qkv_quantization=activation_quantization,
            kimi_linear_full_rank_quantization=matmul_quantization,
            kimi_linear_low_rank_quantization=matmul_quantization,
            kimi_linear_beta_projection_quantization=None,
            kimi_linear_convolution_quantization=None,
            embedding_quantization=weight_quantization,
            prior_embedding_quantization=matmul_quantization,
            unembedding_quantization=matmul_quantization,
            logit_mixing_head_quantization=None,
            adamw_quantization_scales=True,
            attention_implementation="flex_attention",
        )
    )
    model = model.to(device)
    model.load_state_dict(torch.load("models/6m-q4-fp32.tch"))
    model.eval()

    data = CollatedArticlesDataLoader(
        tokens_filename="data/ppmd-bytes.uint8",
        priors_filename="data/ppmd-probs.float16",
        article_boundaries_filename="data/article-boundaries.int32",
        mmap=True,
        epochs=1,
        micro_batch_tokens=micro_batch_tokens,
        gradient_accumulation_steps=1,
        max_article_tokens=max_article_tokens,
        max_merge_tokens=None,
        device=device,
        rank=0,
        world_size=1,
    )

    # save_transformer_outputs(
    #     model=model, data=data, output_filename="data/transformer-probs.float16"
    # )

    n_articles: int = 1024

    save_transformer_outputs_for_article_subset(
        model=model,
        data=data,
        output_filename=f"data/transformer-probs-{n_articles}-articles.bfloat16",
        n_articles=n_articles,
        tokens_filename=f"data/tokens-{n_articles}-articles.uint8",
        article_boundaries_filename=f"data/article-boundaries-{n_articles}-articles.int32",
        seed=42,
    )


if __name__ == "__main__":
    main()
